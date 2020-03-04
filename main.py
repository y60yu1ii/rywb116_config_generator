#!/usr/local/bin/python3
import serial
from serial import SerialException
from time import sleep
import sys, threading
import re
from constants import *
from utils import *


def waitNext(cond):
    cond.acquire()
    cond.wait()


def send(cmd):
    if ser.is_open:
        ser.write(cmd.encode())
        sleep(.2)


def initRYWB():
    global cond
    global threadExit

    send("\x1c")
    send("\x55")
    send("\x31")

    waitNext(cond)
    if threadExit:
        return

    # cmdlist.append(
    #     f'at+rsi_opermode={getOpMode(WIFI_CLI, COEX_BLE)},{feature_bit_map},{tcp_ip_feature_bit_map},{custom_feature_bit_map},{ext_custom_feature_bit_map},{bt_feature_bit_map},{ext_tcp_ip_feature_bit_map},{getBLEFeatureMap(25, 8, 0, 30)}\r\n'
    # )
    cmdlist.append(
        "at+rsi_opermode=851968,0,1,2147483648,2149580800,3221225472,0,1075773440\r\n"
    )
    cmdlist.append(f'at+rsibt_setlocalname={len(deviceName)},{deviceName}\r\n')
    cmdlist.append(f'at+rsibt_getlocalbdaddr?\r\n')
    cmdlist.append(
        f'at+rsibt_addservice=10,{getAttrStr(ServiceUUID)},6,30\r\n')

    for cmd in cmdlist:
        print(f'> {cmd}')
        send(cmd)

    idx = len(cmdlist)

    print("#### waiting for GATT ptr")

    waitNext(cond)
    if threadExit:
        return

    print(f"#### Set GATT with and handler pointer is {ptr} ")
    # read is force in 2803
    cmdlist.append(
        f'at+rsibt_addattribute={ptr},B,2,2803,{PROP_READ},14,{PROP_WRITE},0,0C,00,{getRevAttrStr(rxUUID)}\r\n'
    )
    cmdlist.append(
        f'at+rsibt_addattribute={ptr},C,{BUFF_SIZE},{getAttrStr(rxUUID)},{PROP_WRITE}\r\n'
    )
    cmdlist.append(
        f'at+rsibt_addattribute={ptr},D,2,2803,{PROP_READ},14,{PROP_NOTIFY},0,0E,00,{getRevAttrStr(txUUID)}\r\n'
    )
    cmdlist.append(
        f'at+rsibt_addattribute={ptr},E,{BUFF_SIZE},{getAttrStr(txUUID)},{PROP_NOTIFY}\r\n'
    )

    cmdlist.append(f'at+rsibt_addattribute={ptr},F,2,2902,0A,2,0,0\r\n')

    cmdlist.append(
        f'at+rsibt_addattribute={ptr},10,2,2803,{PROP_READ},14,{PROP_WRITE},0,11,00,{getRevAttrStr(rxOTA)}\r\n'
    )
    cmdlist.append(
        f'at+rsibt_addattribute={ptr},11,{BUFF_SIZE},{getAttrStr(rxOTA)},{PROP_WRITE}\r\n'
    )

    cmdlist.append(
        f'at+rsibt_addattribute={ptr},12,2,2803,{PROP_READ},14,{PROP_NOTIFY},0,13,00,{getRevAttrStr(txOTA)}\r\n'
    )
    cmdlist.append(
        f'at+rsibt_addattribute={ptr},13,{BUFF_SIZE},{getAttrStr(txOTA)},{PROP_NOTIFY}\r\n'
    )

    cmdlist.append(f'at+rsibt_addattribute={ptr},14,2,2902,0A,2,0,0\r\n')

    nameStr = ','.join(hex(ord(x))[2:] for x in deviceName)
    uuidStr = ','.join(list(groupByI(ServiceUUID[4:8], 2))[::-1])
    #put 2, 1, 6 for flags, BLEDR etc.
    cmdlist.append(
        f'at+rsibt_setadvertisedata={len(deviceName) + 1 + 0 + 3 + 2},2,1,6,3,{flag_uuid16_imcplt},{uuidStr},{len(deviceName) + 1},{flag_local_name},{nameStr}\r\n'
    )
    # 2048 for 1/10s
    cmdlist.append(f'at+rsibt_advertise={EN_ADV},128,0,0,0,50,60,0,7\r\n')

    for cmd in cmdlist[idx:]:
        print(f'> {cmd}')
        send(cmd)

    with open(FileName, 'w') as f:
        for cmd in cmdlist:
            f.write("%s\n" % cmd)

    print("end of initRYB")


def checkForHandler(data):
    a = data.split(' ')
    if len(a) > 1:
        b = a[1].split(',')
        if len(b) > 1 and 'A' in b[1]:
            global ptr
            ptr = b[0]
            sleep(0.5)
            print(f"###### OK and ptr is {ptr} {b[1]}")
            global cond
            cond.acquire()
            cond.notify()
            cond.release()


def check(data):
    print('<', data)
    global didConnect, didSubscribed
    if 'Loading Done' in data:
        global cond
        cond.acquire()
        cond.notify()
        cond.release()

    elif 'OK' in data:
        checkForHandler(data)
    elif 'AT+RSIBT_LE_DISCONNECTED' in data:
        # resend broadcast commands
        didConnect = False
        for cmd in cmdlist[-1:]:
            send(cmd)
    elif 'AT+RSIBT_LE_DEVICE_CONNECTED' in data or 'AT+RSIBT_LE_DEVICE_ENHANCE_CONNECTED' in data:
        didConnect = True
        mac = re.search(REG_MAC_ADDR, data)
        if mac is not None:
            global MAC_ADDR
            MAC_ADDR = mac.group()
            print(f"GET MACADDR is {MAC_ADDR}")
            print('send smpreq challenge!!!!')
            sleep(.5)
            send(f'at+rsibt_smpresp=={MAC_ADDR},1\r\n')

    elif 'F,2,0,0' in data:
        didSubscribed = False
    elif 'F,2,1,0' in data:
        didSubscribed = True


def taskSerial():
    print("#### Listening to Serial...")
    while not threadExit:
        while ser.in_waiting:
            data = ser.readline().decode()
            check(data)
    print('\nEnd task serial')


def main():
    try:
        h_serial = threading.Thread(target=taskSerial)
        h_initRYB = threading.Thread(target=initRYWB)

        h_serial.start()
        h_initRYB.start()
        print("Threads start")
        h_initRYB.join()
        h_serial.join()
        ser.close()
    except (KeyboardInterrupt, SystemExit):
        global threadExit
        threadExit = True
        h_initRYB.join()
        h_serial.join()
        ser.close()
        print('\nBye bye!')


if __name__ == '__main__':
    cmdlist = []
    threadExit = False
    didConnect = False
    didSubscribed = False
    readyToSetHandler = False
    cond = threading.Condition()
    ptr = None
    MAC_ADDR = ""

    try:
        ser = serial.Serial(PORT, BAUD)
        main()
    except SerialException:
        print('serial not connected!')
