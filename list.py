from utils import *
p = ports()
for port, desc, hwid in sorted(p):
    print(desc)