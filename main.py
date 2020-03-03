#!/usr/local/bin/python3
import serial
from serial import SerialException
from time import sleep
import sys, threading
from constants import *
from utils import *


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

    cond.acquire()
    cond.wait()

    if threadExit:
        return

    cmdlist.append(
        f'at+rsi_opermode={getOpMode(WIFI_CLI, COEX_BLE)},{feature_bit_map},{tcp_ip_feature_bit_map},{custom_feature_bit_map},{ext_custom_feature_bit_map},{bt_feature_bit_map},{ext_tcp_ip_feature_bit_map},{getBLEFeatureMap(25, 8, 0, 30)}\r\n'
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
    cond.acquire()
    cond.wait()
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

    nameStr = ','.join(hex(ord(x))[2:] for x in deviceName)
    uuidStr = ','.join(list(groupByI(ServiceUUID[4:8], 2))[::-1])
    #put 2, 1, 6 for flags, BLEDR etc.
    cmdlist.append(
        f'at+rsibt_setadvertisedata={len(deviceName) + 1 + 0 + 3 + 2},2,1,6,3,{flag_uuid16_imcplt},{uuidStr},{len(deviceName) + 1},{flag_local_name},{nameStr}\r\n'
    )
    cmdlist.append(f'at+rsibt_advertise={EN_ADV},128,0,0,0,2048,2048,0,7\r\n')

    for cmd in cmdlist[idx:]:
        print(f'> {cmd}')
        send(cmd)

    print("end of initRYB")
    with open(FileName, 'w') as f:
        for cmd in cmdlist:
            f.write("%s\n" % cmd)
    cond.acquire()
    cond.wait()
    if threadExit:
        print('\nEnd initRYB')
        return


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
    global didConnect
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
    elif 'AT+RSIBT_LE_DEVICE_CONNECTED' in data:
        didConnect = True
    elif 'F,2,1,0' in data:
        send(
            f'at+rsibt_setlocalattvalue=E,{convData(str("1234567891011121314151617181920"))}\r\n'
        )


def taskSerial():
    print("#### Listening to Serial...")
    while not threadExit:
        while ser.in_waiting:
            data = ser.readline().decode()
            check(data)
    print('\nEnd task serial')


def main():
    try:
        t = threading.Thread(target=taskSerial)
        t2 = threading.Thread(target=initRYWB)
        t.start()
        t2.start()
        print("Threads start")
        t.join()
        t2.join()
        ser.close()
    except (KeyboardInterrupt, SystemExit):
        global threadExit
        threadExit = True
        global cond
        cond.acquire()
        cond.notify()
        cond.release()

        t.join()
        t2.join()
        ser.close()
        print('\nBye bye!')


if __name__ == '__main__':
    cmdlist = []
    threadExit = False
    didConnect = False
    readyToSetHandler = False
    cond = threading.Condition()
    ptr = None

    try:
        ser = serial.Serial(PORT, BAUD)
        main()
    except SerialException:
        print('serial not connected!')
