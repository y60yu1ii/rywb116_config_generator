import sys
import glob
import serial

def serial_ports():
    if sys.platform.startswith('win'):
        ports = ['COM%s' % (i + 1) for i in range(256)]
    elif sys.platform.startswith('linux') or sys.platform.startswith('cygwin'):
        # this excludes your current terminal "/dev/tty"
        ports = glob.glob('/dev/tty[A-Za-z]*')
    elif sys.platform.startswith('darwin'):
        ports = glob.glob('/dev/tty.*')
    else:
        raise EnvironmentError('Unsupported platform')

    result = []
    for port in ports:
        try:
            s = serial.Serial(port)
            s.close()
            result.append(port)
        except (OSError, serial.SerialException):
            pass
    return result


def flatten(list):
    for i in list:
        for j in i:
            yield j


def groupByI(str, x):
    return (str[i:i + x] for i in range(0, len(str), x))


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
