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
    global cond, threadExit

    send("\x1c")
    send("\x55")
    send("\x31")

    waitNext(cond)
    if threadExit:
        return

    cmdlist.append(
        f'{AT_OPMODE}={getOpMode(WIFI_CLI, COEX_BLE)},{feature_bit_map},{tcp_ip_feature_bit_map},{custom_feature_bit_map},{ext_custom_feature_bit_map},{bt_feature_bit_map},{ext_tcp_ip_feature_bit_map},{getBLEFeatureMap(25, 8, 0, 30)}\r\n'
    )
    cmdlist.append(f'{AT_LOCALNAME}={len(deviceName)},{deviceName}\r\n')
    cmdlist.append(f'at+rsibt_getlocalbdaddr?\r\n')
    cmdlist.append(
        f'{AT_ADD_SERVICE}=10,{getAttrStr(ServiceUUID)},6,30\r\n')

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
        f'{AT_ADD_ATTR}={ptr},B,2,{ATT_DECL_CHARACTERISTIC},{PROP_READ},14,{PROP_WRITE},0,0C,00,{getRevAttrStr(rxUUID)}\r\n'
    )
    cmdlist.append(
        f'{AT_ADD_ATTR}={ptr},C,{BUFF_SIZE},{getAttrStr(rxUUID)},{PROP_WRITE}\r\n'
    )
    cmdlist.append(
        f'{AT_ADD_ATTR}={ptr},D,2,{ATT_DECL_CHARACTERISTIC},{PROP_READ},14,{PROP_NOTIFY},0,0E,00,{getRevAttrStr(txUUID)}\r\n'
    )
    cmdlist.append(
        f'{AT_ADD_ATTR}={ptr},E,{BUFF_SIZE},{getAttrStr(txUUID)},{PROP_NOTIFY}\r\n'
    )

    cmdlist.append(f'{AT_ADD_ATTR}={ptr},F,2,{UUIDCCCD},0A,2,0,0\r\n')

    cmdlist.append(
        f'{AT_ADD_ATTR}={ptr},10,2,{ATT_DECL_CHARACTERISTIC},{PROP_READ},14,{PROP_WRITE},0,11,00,{getRevAttrStr(rxOTA)}\r\n'
    )
    cmdlist.append(
        f'{AT_ADD_ATTR}={ptr},11,{BUFF_SIZE},{getAttrStr(rxOTA)},{PROP_WRITE}\r\n'
    )

    cmdlist.append(
        f'{AT_ADD_ATTR}={ptr},12,2,{ATT_DECL_CHARACTERISTIC},{PROP_READ},14,{PROP_NOTIFY},0,13,00,{getRevAttrStr(txOTA)}\r\n'
    )
    cmdlist.append(
        f'{AT_ADD_ATTR}={ptr},13,{BUFF_SIZE},{getAttrStr(txOTA)},{PROP_NOTIFY}\r\n'
    )

    cmdlist.append(f'{AT_ADD_ATTR}={ptr},14,2,{UUIDCCCD},0A,2,0,0\r\n')

    nameStr = ','.join(hex(ord(x))[2:] for x in deviceName)
    uuidStr = ','.join(list(groupByI(ServiceUUID[4:8], 2))[::-1])
    #put 2, 1, 6 for flags, BLEDR etc.
    cmdlist.append(
        f'{AT_SET_ADV}={len(deviceName) + 1 + 0 + 3 + 2},2,1,6,3,{flag_uuid16_imcplt},{uuidStr},{len(deviceName) + 1},{flag_local_name},{nameStr}\r\n'
    )
    # 2048 for 1/10s
    cmdlist.append(f'{AT_ADV}={EN_ADV},128,0,0,0,50,60,0,7\r\n')

    for cmd in cmdlist[idx:]:
        print(f'> {cmd}')
        send(cmd)

    with open(FileName, 'w') as f:
        for cmd in cmdlist:
            f.write("%s\n" % cmd)

    # print("end of initRYB")


def check(data):
    print('<', data)
    global didConnect, didSubscribed, cond, MAC_ADDR
    if re.match("^(Loading Done)", data) is not None:
        cond.acquire()
        cond.notify()
        cond.release()

    elif re.match("^(OK [A-Z0-9]{5},A)", data) is not None:
        h = re.search("[A-Z0-9]{5}", data)
        print(f"{h.group()}")
        global ptr
        ptr = h.group()
        cond.acquire()
        cond.notify()
        cond.release()

    # elif 'AT+RSIBT_LE_DISCONNECTED' in data:
    elif re.match(REGX_DISCONN, data) is not None:
        didConnect = False
        MAC_ADDR = re.search(REGX_MAC, data).group()
        print(f"{MAC_ADDR} disconnected, re-broadcasting")
        # resend broadcast commands
        for cmd in cmdlist[-1:]:
            send(cmd)
    elif re.match(REGX_CONN, data) is not None:
        didConnect = True
        MAC_ADDR = re.search(REGX_MAC, data).group()
        print(f"{MAC_ADDR} connected")

    elif re.match(REGX_SUBSCR, data) is not None:
        didSubscribed = data.split(',')[-2] == '1'
        print(f"handler {data.split(',')[-4]} is {'Subscribed' if didSubscribed else 'Unsubscribed'}")


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
