#!/usr/local/bin/python3
import serial
from serial import SerialException
from time import sleep
import sys, threading
import re
from constants import *
from utils import *
import wx
from pubsub import pub

TITLE = "RYWB116 Setting"
PORT_LIST=["port"]
_PORT = "port"
dh = 500
dw = 500

class MyFrame(wx.Frame):
    def __init__(self,parent=None):
        super(MyFrame, self).__init__(parent,-1,TITLE,size=(dw, dh))
        panel = wx.Panel(self,-1)
        self.pChoice = wx.Choice(panel, -1, pos=(10, 10), size=(250, -1),choices=PORT_LIST)
        self.pChoice.Bind(wx.EVT_CHOICE, self.onChoice)

        self.button = wx.Button(panel,-1,"GO",pos=(dw - 90,10))
        self.Bind(wx.EVT_BUTTON,self.OnClick,self.button)
        self.button.SetDefault()

        self.textpanel = wx.TextCtrl(panel,-1,"## LOG ##", size=(dw - 20,400), pos=(10, 40), style=wx.TE_MULTILINE|wx.TE_READONLY)


        pub.subscribe(self.recive, 'object.added')
        pub.subscribe(self.reciveThread, 'thread.input')

        f = threading.Thread(target=findPort)
        f.daemon = True
        f.start()
        print("Find port...")
    
    def onChoice(self, evt):
        global _PORT
        _PORT = evt.GetString()
        print("choice is port as", _PORT)

    def OnClick(self,event):
        if _PORT == "port" :
            return
        else:
            callUI("go", "0")


    def recive(self,data, extra1, extra2=None):
        print(data)
        print(extra1)
        if extra2:
            print(extra2)
        # self.inputText.Value += str(data)
        self.textpanel.Value += str(data)

    def reciveThread(self, tag, data):
        wx.CallAfter(self.updateUI, tag, data)

    def updateUI(self, tag, data):
        if tag == 'log':
            self.textpanel.Value += ("\n" + str(data))
        elif tag == 'port':
            self.pChoice.Clear()
            self.pChoice.AppendItems(PORT_LIST)
        elif tag == 'go':
            print("go with port ", PORT)
            self.button.Disable()
            s = threading.Thread(target=taskSerial)
            i = threading.Thread(target=initRYWB)

            s.start()
            i.start()

def findPort():
    global PORT_LIST
    PORT_LIST = serial_ports()
    callUI("port", "0")

def taskSerial():
    try:
        ser = serial.Serial(_PORT, BAUD)
        callUI("log","Serial Ready!!" + str(ser.is_open))
    except SerialException:
        callUI("log", "Serial is not connect!!")

    while not threadExit:
        while ser.in_waiting:
            data = ser.readline().decode()
            print(">", data)
            check(data)

def send(cmd):
    ser = serial.Serial(_PORT, BAUD)
    if ser.is_open:
        ser.write(cmd.encode())
        sleep(.2)

def callUI(tag, data):
    pub.sendMessage('thread.input', tag=tag, data=data)

def waitNext(cond):
    cond.acquire()
    cond.wait()

def initRYWB():
    print("init RYWB")
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
        callUI("log", (">"+cmd))
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
        callUI("log", (">"+cmd))
        send(cmd)

    # with open(FileName, 'w') as f:
    #     for cmd in cmdlist:
    #         f.write("%s\n" % cmd)

def check(data):
    callUI("log", ("< "+data))
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

if __name__ == '__main__':
    cmdlist = []
    threadExit = False
    didConnect = False
    didSubscribed = False
    readyToSetHandler = False
    cond = threading.Condition()
    ptr = None
    MAC_ADDR = ""

    app = wx.App()
    frm = MyFrame()
    frm.Show()
    app.MainLoop()