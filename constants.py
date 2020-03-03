PORT = '/dev/cu.SLAB_USBtoUART'
BAUD = 115200
BUFF_SIZE = 128

deviceName = "Device_Name"
ServiceUUID = '6E400001-B5A3-F393-E0A9-E50E24DCCA9E'
rxUUID = '6E400002-B5A3-F393-E0A9-E50E24DCCA9E'
txUUID = '6E400003-B5A3-F393-E0A9-E50E24DCCA9E'
FileName = "scripts.txt"

# WIFI OPMODE VALUES
WIFI_CLI = 0
WIFI_DIRECT = 1
WIFI_ENTPRS_SECUR_CLI = 2
WIFI_AP = 6
PER = 8
WIFI_CONCURNT = 9

# COEX OPMODE VALUES
COEX_WLAN = 1
COEX_ZIGBEE = 2
COEX_WLAN_ZIGBEE = 3
COEX_BLUETOOTH = 4
COEX_WIFI_BLUETOOTH = 5
COEX_BLUETOOTH_ZIGBEE = 6
COEX_WLAN_BLUETOOTH_ZIGBEE = 7
COEX_BLUETOOTH_DUAL = 8
COEX_WLAN_BLUETOOTH_DUAL = 9
COEX_ZIGBEE_BLUETOOTH_DUAL = 10
COEX_WIFI_ZIGBEE_BLUETOOTH_DUAL = 11
COEX_BLE = 12
COEX_WIFI_BLE = 13
COEX_BLE_ZIGBEE = 14
COEX_WIFI_BLE_ZIGBEE = 15

feature_bit_map = 0
tcp_ip_feature_bit_map = 1
custom_feature_bit_map = 2147483648
ext_custom_feature_bit_map = 2150121472
bt_feature_bit_map = 3221225472
ext_tcp_ip_feature_bit_map = 0

# Advertise
DISABLE_ADV = 0
EN_ADV = 1

# BLE
flag_local_name = 9
flag_flags = 1
flag_uuid16_imcplt = 2

# Characteristic propoerty

PROP_BROADCAST = 1  # boradcase
PROP_READ = 2  # read
# PROP_BROAD_READ = 3  # broadcast and read 1 + 2
PROP_WnRESP = 4  # write without response
# PROP_BROAD_W_nRESP = 5  # boradcast and write without response 1+ 4
# PROP_READ_W_nRESP = 6  # boradcast and write without response 2+4
PROP_WRITE = 8  # write with response
# PROP_BROAD_WRITE = 9  # boradcast and write 1 + 8
PROP_NOTIFY = 10  # notify
PROP_INDICATE = 20  # indicate
PROP_AUTH_W = 40  # authenticated signed wrties
PROP_EXTEND = 80  # extended properties
