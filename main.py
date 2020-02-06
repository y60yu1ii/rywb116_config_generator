#!/usr/local/bin/python3
import serial
from time import sleep
import sys
from constants import *
from utils import *

ser = serial.Serial(PORT, BAUD)

cmdlist = []
didSetGATT = False
didConnect = False


# conver input data
def convData(data):
    s = ','.join(hex(ord(x))[2:] for x in data)
    return str(f'{len(data)},{s}')


# Function code area
def getOpMode(wifi_oper_mode, coex_mode):
    return (wifi_oper_mode | (coex_mode << 16))


def getBLEFeatureMap(attrs, gatts, slaves, tx_index):
    return (attrs | gatts << 8 | slaves << 12 | tx_index << 16)
    # Range for the BLE Tx Power Index is 1 to 75 (0, 32 index is invalid)
    # 1 - 31 BLE -0DBM Mode
    # 33 - 63 BLE- 10DBM Mode
    # 64- 75 BLE - HP Mode.


def getAttrStr(uuid):
    e = uuid.split('-')
    m0 = ',-'.join(e[:-1])
    m = list(groupByI(''.join(e[-1:]), 2))[::-1]
    m1 = ','.join(m[-2:] + m[:4])
    return str(f'{m0},{m1}')


def getRevAttrStr(uuid):
    e = list(groupByI(''.join(uuid.split('-')), 2))
    m0 = ','.join(e[:4][::-1])
    m2 = ','.join(e[-4:][::-1])
    m1 = ','.join(list(flatten(list(groupByI(e[4:-4][::-1], 2))[::-1])))
    return str(f'{m0},{m1},{m2}')


def send(cmd):
    ser.write(cmd.encode())
    sleep(.2)


def wakeRYWB():
    send("\x1c")
    send("\x55")
    send("\x31")


def setGATT(ptr, h):
    idx = len(cmdlist)
    # read is force in 2803
    cmdlist.append(
        f'at+rsibt_addattribute={ptr},B,2,2803,{PROP_READ},14,{PROP_WRITE},0,0C,00,{getRevAttrStr(rxUUID)}\r\n'
    )
    cmdlist.append(
        f'at+rsibt_addattribute={ptr},C,{BUFF_SIZE},{getAttrStr(rxUUID)},{PROP_WRITE}\r\n'
    )
    cmdlist.append(
        f'at+rsibt_addattribute={ptr},D,2,2803,2,14,{PROP_NOTIFY},0,0E,00,{getRevAttrStr(txUUID)}\r\n'
    )
    cmdlist.append(
        f'at+rsibt_addattribute={ptr},E,{BUFF_SIZE},{getAttrStr(txUUID)},{PROP_NOTIFY}\r\n'
    )

    cmdlist.append(f'at+rsibt_addattribute={ptr},F,2,2902,0A,2,0,0\r\n')

    nameStr = ','.join(hex(ord(x))[2:] for x in deviceName)
    uuidStr = ','.join(list(groupByI(ServiceUUID[4:8], 2))[::-1])
    #put 2, 1, 6 for flags, BLEDR etc.
    cmdlist.append(
        f'at+rsibt_setadvertisedata={len(deviceName) + 1 + 0 + 3 + 2},2,1,6,3,{flag_uuid16_imcplt},{uuidStr},{len(deviceName) + 1},{flag_local_name},{nameStr}\r\n'
    )
    cmdlist.append(f'at+rsibt_advertise={EN_ADV},128,0,0,0,2048,2048,0,7\r\n')

    global didSetGATT
    didSetGATT = True

    for cmd in cmdlist[idx:]:
        print(f'> {cmd}')
        send(cmd)

    with open(FileName, 'w') as f:
        for cmd in cmdlist:
            f.write("%s\n" % cmd)


def initRYWB():
    wakeRYWB()
    sleep(1)
    cmdlist.append(
        f'at+rsi_opermode={getOpMode(WIFI_CLI, COEX_BLE)},{feature_bit_map},{tcp_ip_feature_bit_map},{custom_feature_bit_map},{ext_custom_feature_bit_map},{bt_feature_bit_map},{ext_tcp_ip_feature_bit_map},{getBLEFeatureMap(25, 8, 0, 30)}\r\n'
    )
    cmdlist.append(f'at+rsibt_setlocalname={len(deviceName)},{deviceName}\r\n')
    cmdlist.append(f'at+rsibt_getlocalbdaddr?\r\n')
    cmdlist.append(
        f'at+rsibt_addservice=10,{getAttrStr(ServiceUUID)},6,30\r\n')

    for cmd in cmdlist:
        print(cmd)
        send(cmd)

    with open(FileName, 'w') as f:
        for cmd in cmdlist:
            f.write("%s\n" % cmd)


def check(data):
    global didConnect
    if "OK" in data:
        a = data.split(' ')
        if len(a) > 1:
            b = a[1].split(',')
            if len(b) > 1 and not didSetGATT:
                setGATT(b[0], b[1])
    if 'AT+RSIBT_LE_DISCONNECTED' in data:
        # resend broadcast commands
        didConnect = False
        for cmd in cmdlist[-1:]:
            send(cmd)
    if 'AT+RSIBT_LE_DEVICE_CONNECTED' in data:
        didConnect = True
    if 'F,2,1,0' in data:
        send(
            f'at+rsibt_setlocalattvalue=E,{convData(str("1234567891011121314151617181920"))}\r\n'
        )


def main():
    initRYWB()
    try:
        while True:
            while ser.in_waiting:
                data = ser.readline().decode()
                print('<', data)
                check(data)
    except KeyboardInterrupt:
        ser.close()
        print('\nBye bye!')


if __name__ == '__main__':
    main()