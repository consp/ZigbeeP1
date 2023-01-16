# compile with py -m mpy_cross -msmall-int-bits=31 -o main.mpy -mno-unicode main.py
# optionally use cache lookups, change heap size or optimization level
from binascii import hexlify, unhexlify
import machine
import sys
import utime
import xbee
import micropython
import gc


###############################################################
# Variables, change these if you want to.                     #
###############################################################

NAME = "XBee P1"
DEBUG = False

# Always publish data, not just on change
ALWAYS_PUBLISH = True
# perform p1 read + send every N seceonds
CYCLE_TIME = 15

# Pin definitions
repl_button = machine.Pin(machine.Pin.board.D5, machine.Pin.IN, machine.Pin.PULL_UP)
led = machine.Pin(machine.Pin.board.D4, machine.Pin.OUT)
RTS = machine.Pin(machine.Pin.board.D9, machine.Pin.OUT)

###############################################################
# None "editable" code from here                              #
###############################################################

# DSMR V5 testdata from ndokter parser: https://github.com/ndokter/dsmr_parser/blob/master/test/example_telegrams.py
# switch out to do DEBUG test runs
TESTDATA = b""
#TESTDATA = b"""/ISk5\\2MT382-1000\r\n\r\n1-3:0.2.8(50)\r\n0-0:1.0.0(170102192002W)\r\n0-0:96.1.1(4B384547303034303436333935353037)\r\n1-0:1.8.1(000004.426*kWh)\r\n1-0:1.8.2(000002.399*kWh)\r\n1-0:2.8.1(000002.444*kWh)\r\n1-0:2.8.2(000000.000*kWh)\r\n0-0:96.14.0(0002)\r\n1-0:1.7.0(00.244*kW)\r\n1-0:2.7.0(00.000*kW)\r\n0-0:96.7.21(00013)\r\n0-0:96.7.9(00000)\r\n1-0:99.97.0(0)(0-0:96.7.19)\r\n1-0:32.32.0(00000)\r\n1-0:52.32.0(00000)\r\n1-0:72.32.0(00000)\r\n1-0:32.36.0(00000)\r\n1-0:52.36.0(00000)\r\n1-0:72.36.0(00000)\r\n0-0:96.13.0()\r\n1-0:32.7.0(0230.0*V)\r\n1-0:52.7.0(0230.0*V)\r\n1-0:72.7.0(0229.0*V)\r\n1-0:31.7.0(0.48*A)\r\n1-0:51.7.0(0.44*A)\r\n1-0:71.7.0(0.86*A)\r\n1-0:21.7.0(00.070*kW)\r\n1-0:41.7.0(00.032*kW)\r\n1-0:61.7.0(00.142*kW)\r\n1-0:22.7.0(00.000*kW)\r\n1-0:42.7.0(00.000*kW)\r\n1-0:62.7.0(00.000*kW)\r\n0-1:24.1.0(003)\r\n0-1:96.1.0(3232323241424344313233343536373839)\r\n0-1:24.2.1(170102161005W)(00000.107*m3)\r\n0-2:24.1.0(003)\r\n0-2:96.1.0()\r\n!6EEE"""

CRC_TABLE = [
    0x0000,0xC0C1,0xC181,0x0140,0xC301,0x03C0,0x0280,0xC241,0xC601,0x06C0,0x0780,0xC741,0x0500,
    0xC5C1,0xC481,0x0440,0xCC01,0x0CC0,0x0D80,0xCD41,0x0F00,0xCFC1,0xCE81,0x0E40,0x0A00,0xCAC1,
    0xCB81,0x0B40,0xC901,0x09C0,0x0880,0xC841,0xD801,0x18C0,0x1980,0xD941,0x1B00,0xDBC1,0xDA81,
    0x1A40,0x1E00,0xDEC1,0xDF81,0x1F40,0xDD01,0x1DC0,0x1C80,0xDC41,0x1400,0xD4C1,0xD581,0x1540,
    0xD701,0x17C0,0x1680,0xD641,0xD201,0x12C0,0x1380,0xD341,0x1100,0xD1C1,0xD081,0x1040,0xF001,
    0x30C0,0x3180,0xF141,0x3300,0xF3C1,0xF281,0x3240,0x3600,0xF6C1,0xF781,0x3740,0xF501,0x35C0,
    0x3480,0xF441,0x3C00,0xFCC1,0xFD81,0x3D40,0xFF01,0x3FC0,0x3E80,0xFE41,0xFA01,0x3AC0,0x3B80,
    0xFB41,0x3900,0xF9C1,0xF881,0x3840,0x2800,0xE8C1,0xE981,0x2940,0xEB01,0x2BC0,0x2A80,0xEA41,
    0xEE01,0x2EC0,0x2F80,0xEF41,0x2D00,0xEDC1,0xEC81,0x2C40,0xE401,0x24C0,0x2580,0xE541,0x2700,
    0xE7C1,0xE681,0x2640,0x2200,0xE2C1,0xE381,0x2340,0xE101,0x21C0,0x2080,0xE041,0xA001,0x60C0,
    0x6180,0xA141,0x6300,0xA3C1,0xA281,0x6240,0x6600,0xA6C1,0xA781,0x6740,0xA501,0x65C0,0x6480,
    0xA441,0x6C00,0xACC1,0xAD81,0x6D40,0xAF01,0x6FC0,0x6E80,0xAE41,0xAA01,0x6AC0,0x6B80,0xAB41,
    0x6900,0xA9C1,0xA881,0x6840,0x7800,0xB8C1,0xB981,0x7940,0xBB01,0x7BC0,0x7A80,0xBA41,0xBE01,
    0x7EC0,0x7F80,0xBF41,0x7D00,0xBDC1,0xBC81,0x7C40,0xB401,0x74C0,0x7580,0xB541,0x7700,0xB7C1,
    0xB681,0x7640,0x7200,0xB2C1,0xB381,0x7340,0xB101,0x71C0,0x7080,0xB041,0x5000,0x90C1,0x9181,
    0x5140,0x9301,0x53C0,0x5280,0x9241,0x9601,0x56C0,0x5780,0x9741,0x5500,0x95C1,0x9481,0x5440,
    0x9C01,0x5CC0,0x5D80,0x9D41,0x5F00,0x9FC1,0x9E81,0x5E40,0x5A00,0x9AC1,0x9B81,0x5B40,0x9901,
    0x59C0,0x5880,0x9841,0x8801,0x48C0,0x4980,0x8941,0x4B00,0x8BC1,0x8A81,0x4A40,0x4E00,0x8EC1,
    0x8F81,0x4F40,0x8D01,0x4DC0,0x4C80,0x8C41,0x4400,0x84C1,0x8581,0x4540,0x8701,0x47C0,0x4680,
    0x8641,0x8201,0x42C0,0x4380,0x8341,0x4100,0x81C1,0x8081,0x4040
]


# globals
STATUS = 0
SERVER_NWK = None
SERVER_ADDR = None
first = True


###############################################################
# Endpoints, these are used for the zigbee communication.     #
###############################################################

ENDPOINTS = {
'1': {
    'endpoint': 1,
    'profile_id': 0x0104,
    'device_id': 0x0007,
    'version': 0,
    'input_clusters': [
        0, # basic 0x0000
        1794, # seMetering 0x0702
        2820, # haElectricalMeasurement
    ],
    'output_clusters': [
    ],
},
'2': {
    'endpoint': 2,
    'profile_id': 0x0104,
    'device_id': 0x0007,
    'version': 0,
    'input_clusters': [
        1794, # seMetering 0x0702
    ],
    'output_clusters': [
    ],
},
}


###############################################################
# Global attributes, change these if you must                 #
###############################################################

ATTRIBUTES = {
 '0': [0x20, int(8).to_bytes(1, 'little')],
 '1': [0x20, int(0).to_bytes(1, 'little')],
 '2': [0x20, int(0).to_bytes(1, 'little')],
 '3': [0x20, int(0).to_bytes(1, 'little')],
 '4': [0x42, b"consp"],
 '5': [0x42, b"Zigbee P1 Meter"],
 '6': [0x42, b"2023-01-15"],
 '7': [0x30, int(4).to_bytes(1, 'little')],
 '8': [0x30, b"\x00"],
 '9': [0x30, b"\xff"],
 '16384': [0x42, b"v0.1"],
}

###############################################################
# Smart energy endpoint and variables.                        #
###############################################################
RP_ENERGY_SUM =     [0x0702, 0x0000, 0x25, None]
RP_ENERGY_T1 =      [0x0702, 0x0100, 0x25, None]
RP_ENERGY_T2 =      [0x0702, 0x0102, 0x25, None]
RP_ENERGY_D_T1 =    [0x0702, 0x0101, 0x25, None]
RP_ENERGY_D_T2 =    [0x0702, 0x0103, 0x25, None]
RP_ENERGY_STATUS =  [0x0702, 0x0200, 0x18, b"\x00"]
RP_ENERGY_UOM =     [0x0702, 0x0300, 0x30, b"\x00"]
RP_ENERGY_MUL =     [0x0702, 0x0301, 0x22, int(1).to_bytes(3, 'little')]
RP_ENERGY_DIV =     [0x0702, 0x0302, 0x22, int(1000).to_bytes(3, 'little')]

RP_GAS_SUM =        [0x0702, 0x0000, 0x25, None] # gas is at point 2
RP_GAS_T1 =         [0x0702, 0x0100, 0x25, None]
RP_GAS_STATUS =     [0x0702, 0x0200, 0x18, b"\x00"]
RP_GAS_UOM =        [0x0702, 0x0300, 0x30, b"\x01"]
RP_GAS_MUL =        [0x0702, 0x0301, 0x22, int(1).to_bytes(3, 'little')]
RP_GAS_DIV =        [0x0702, 0x0302, 0x22, int(1000).to_bytes(3, 'little')]

RP_GAS =            [0x0702, 0x0000, 0x25, None]

###############################################################
# Energy endpoints and veriables.                             #
###############################################################
RP_POWER_SUM = [0x0b04, 0x0304, 0x2b, None]
RP_L1_A = [0x0b04, 0x0508, 0x21, None]
RP_L1_V = [0x0b04, 0x0505, 0x21, None]
RP_L1_P = [0x0b04, 0x050b, 0x21, None]
RP_L2_A = [0x0b04, 0x0908, 0x21, None]
RP_L2_V = [0x0b04, 0x0905, 0x21, None]
RP_L2_P = [0x0b04, 0x090b, 0x21, None]
RP_L3_A = [0x0b04, 0x0a08, 0x21, None]
RP_L3_V = [0x0b04, 0x0a05, 0x21, None]
RP_L3_P = [0x0b04, 0x0a0b, 0x21, None]
RP_V_MUL = [0x0b04, 0x0600, 0x21, int(1).to_bytes(2, 'little')]
RP_V_DIV = [0x0b04, 0x0601, 0x21, int(10).to_bytes(2, 'little')]
RP_A_MUL = [ 0x0b04, 0x0602, 0x21, int(1).to_bytes(2, 'little')]
RP_A_DIV = [ 0x0b04, 0x0603, 0x21, int(100).to_bytes(2, 'little')]
RP_P_MUL = [ 0x0b04, 0x0402, 0x23, int(1).to_bytes(4, 'little')]
RP_P_DIV = [ 0x0b04, 0x0403, 0x23, int(1).to_bytes(4, 'little')]
RP_PHASES = [ 0x0b04, 0x0000, 0x1b, int(0b001001).to_bytes(4, 'little')] # only L1


# filled with values
REPORTING_ATTRIBUTES = []

def debug(*args, **kwargs):
    if DEBUG:
        print(*args, **kwargs)


def simple_descriptor(data):
    response = \
        data['endpoint'].to_bytes(1, 'little') + \
        data['profile_id'].to_bytes(2, 'little') + \
        data['device_id'].to_bytes(2, 'little') + \
        (data['version'] << 4).to_bytes(1, 'little') + \
        len(data['input_clusters']).to_bytes(1, 'little') + \
        b"".join([i.to_bytes(2, 'little') for i in data['input_clusters']]) + \
        len(data['output_clusters']).to_bytes(1, 'little') + \
        b"".join([i.to_bytes(2, 'little') for i in data['output_clusters']])
    return response

def attribute_value(data):
    return b"" + data[0].to_bytes(1, 'little') + (data[1] if data[0] not in [0x42] else (len(data[1]).to_bytes(1, 'little') + data[1]))

def blink():
    led(led.value() ^ 1)

def process_zdo(cluster, data, sender):
    if cluster == 0x0004:
        debug("Request simple descriptor")
        transaction = data[0:1]
        nwk_address = data[1:3]
        ep = data[3]
        descriptor = simple_descriptor(ENDPOINTS['%d' % ep])
        debug("Request simple descriptor %d" % (ep))
        response = transaction + "\x00" + nwk_address + len(descriptor).to_bytes(1, 'little') + descriptor
        debug("EP response: %s" % (hexlify(response).decode()))
        xbee.transmit(sender, response, source_ep=0, dest_ep=0, cluster=0x8004, profile=0)

    elif cluster == 0x0005:  # req active endpoints
        # 2 octets with network address, we ignore these as we are the endpoint already
        # respond with ep_rsp 0x8005
        debug("EP Req")
        transaction = data[0:1]
        nwk_address = data[1:3]  # collect network address
        response = transaction + b"\x00" + nwk_address + len(ENDPOINTS).to_bytes(1, 'little') + bytes([ENDPOINTS[i]['endpoint'] for i in ENDPOINTS])
        nwk_address_int = int.from_bytes(nwk_address, 'little')
        debug("EP response nwk %d: %s" % (nwk_address_int, hexlify(response).decode()))
        xbee.transmit(sender, response, source_ep=0, dest_ep=0, cluster=0x8005, profile=0)
    elif cluster == 0x0021: # bind request
        transaction = data[0:1]
        src = data[1:9]
        src_ep = data[9]
        cluster_id = data[10:12]
        addr_type = data[12]
        dst = data[13:21]
        dst_ep = data[21]
        debug("Bind Req %d to %d" % (src_ep, dst_ep))
        # do nothing now
        response = transaction + b"\x00"
        xbee.transmit(sender, response, source_ep=0, dest_ep=0, cluster=0x8021, profile=0)
    elif cluster == 0x0022: # unbind request
        debug("Unbind Req")
        transaction = data[0:1]
        # do nothing now
        response = transaction + b"\x00"
        xbee.transmit(sender, response, source_ep=0, dest_ep=0, cluster=0x8022, profile=0)
    elif cluster == 0x8001:  # ZDP IEEE ADDR
        # 84 00 a096b626004b1200 0000
        global SERVER_ADDR
        global SERVER_NWK
        SERVER_ADDR = data[2:10]
        SERVER_NWK = int.from_bytes(data[10:12], 'little')
    elif cluster == 0x8002:  # ZDP Node Desc
        pass # aka ignore
    else:
        debug("cluster: %04X, data: %s" % (cluster, hexlify(data).decode()))


def process_zcl(cluster, profile, data, sender, src_ep=0, dst_ep=0):
    # FC, TSQ, CID, payload
    if len(data) < 3:
        print("No ZCL Frame")
    frame_control = data[0]
    sequence = data[1]
    cid = data[2]

    # decode FC
    fc_type =       (frame_control & 0x03)
    fc_ms =         (frame_control & 0x04) >> 2
    fc_direction =  (frame_control & 0x08) >> 3
    fc_ddr =        (frame_control & 0x10) >> 4

    if cid == 0x00:
        # read attributes
        attributes = [int.from_bytes(data[n:n+2], 'little') for n in range(3, len(data), 2)]
        header = b"\x10" + sequence.to_bytes(1, 'little') + "\x01"
        response = b""
        for item in attributes:
            debug("Reading attribute %d %04X" % (item, item))
            astring = '%d' % (item)
            if astring in ATTRIBUTES:
                response = response + item.to_bytes(2, 'little') + "\x00" + attribute_value(ATTRIBUTES[astring])
            else:
                response = response + item.to_bytes(2, 'little') + "\x86"
        # 109801 0400 00 05 636f6e7370
        response = header + response
        debug("Response: %s" % (hexlify(response).decode()))
        xbee.transmit(sender, response, source_ep=src_ep, dest_ep=dst_ep, cluster=cluster, profile=profile)
    elif cid == 0x0b:
        debug("Received response to command %02X status %02X" % (data[3], data[4]))
        # after first respose only send updates
        global first
        first = False
    else:
        debug("c/p %04X %04X" % (cluster, profile))
        debug("FC: %02X SQ: %02X CID: %02X" % (frame_control, sequence, cid))
        debug("UNKNOWN CID: %02X" % (cid))

# callbacks
def callback_status(status):
    global STATUS
    print("Received status: {:02X}".format(status))
    STATUS = status

def callback_receive(data):
    sender = data['sender_eui64']
    nwk = data['sender_nwk']
    payload = data['payload']
    profile = data['profile']
    cluster = data['cluster']
    s_ep = data['source_ep']
    d_ep = data['dest_ep']

    if profile == 0x0000: # zdo
        debug("ZDO Message")
        process_zdo(cluster, payload, sender)
    elif profile == 0x0104:
        process_zcl(cluster, profile, payload, sender, src_ep=d_ep, dst_ep=s_ep)
    else:
        debug("UNKNOWN profile: %04X" % (profile))
        debug("sender: %s, %d/%04X" % (hexlify(sender).decode(), nwk, nwk))
        debug("payload: %s" % (hexlify(payload).decode()))
        debug("c/p: 0x%04X, %d // 0x%04X, %d" % (cluster, cluster, profile, profile))
        debug("ep: %d, %d" % (s_ep, d_ep))
        #debug(data)


# register callbacks
xbee.modem_status.callback(callback_status)
xbee.receive_callback(callback_receive)

SEQUENCE_NR = 0
# Processing of data and sending
def zcl_send_report(sink, endpoint, profile, attributes):
    # construct header, sequence is global
    if len(attributes) == 0:
        return
    global SEQUENCE_NR
    header = b"\x00" + SEQUENCE_NR.to_bytes(1, 'little') + "\x0a"

    # data [2xAID, DATA_TYPE, DATA]
    response = b""
    clusters = []
    for att in attributes:
        if att[0] not in clusters:
            clusters.append(att[0])

    for cluster in clusters:
        for item in attributes:
            if item[0] != 0 and item[0] == cluster: # skip illigal values and not in cluster
                response = response + item[1].to_bytes(2, 'little') + item[2].to_bytes(1, 'little') + item[3]
        try:
            debug("Transmitting to ep %d cluster %04X %s" % (endpoint, cluster, hexlify(header + response).decode()))
            xbee.transmit(sink, header + response, source_ep=endpoint, dest_ep=1, cluster=cluster, profile=profile)
            SEQUENCE_NR += 1
            if SEQUENCE_NR > 255:
                SEQUENCE_NR = 0
        except:
            pass


# CRC16 with A001 poly
def crc16(data):
    crc = 0x0000
    for c in data:
        crc = CRC_TABLE[(crc ^ c) & 0xFF] ^ ((crc >> 8) & 0xFF);
    return crc

# setup
xbee.atcmd("NI", NAME)
# xbee.atcmd("CE", 0) # join cannot be set
xbee.atcmd("AO", 0b00001110)
xbee.atcmd("ID", 0) # broadcast
xbee.atcmd("ZS", 2) # zigbee pro
xbee.atcmd("NJ", 255) # join time
xbee.atcmd("JN", 1) # join network enabled
xbee.atcmd("EO", 0x1B) # make sure we can rejoin

micropython.kbd_intr(-1) # disable ctrl-c
# clear rts
RTS(0)

cntr = 0

# wait for network to wake up
print("Connecting to network ", end="")
while STATUS != 2:
    print("%d" % STATUS, end="")
    utime.sleep_ms(1000)


def send_data():
    zcl_send_report(xbee.ADDR_COORDINATOR, 1, 0x0104, REPORTING_ATTRIBUTES)
    zcl_send_report(xbee.ADDR_COORDINATOR, 2, 0x0104, REPORTING_ATTRIBUTES2)


def read_p1():
    # read the p1 port by raising RTS
    RTS(1)
    data = None
    timeout = 0
    finished = False
    # stdin since we cannot control the primary uart
    while timeout < 10 and not finished:
        chars = sys.stdin.buffer.read()
        if chars is not None and len(chars) > 0 and b"/" in chars:
            # start found, collect until ! and then 4 more and dump data to process_zcl
            data = chars[chars.index(b"/"):] # strip !
            timeout2 = 0
            while True and timeout2 < 100:
                chars = sys.stdin.buffer.read()
                if chars is not None:
                    data = data + chars
                    if b'!' in chars:
                        break
                timeout2 = timeout2 + 1
                utime.sleep_ms(10)
            # ! found, we think
            timeout3 = 0
            while data.index(b"!") < len(data) - 4 and timeout3 < 10:
                utime.sleep_ms(10) # more thant enough to fill buffer
                chars = sys.stdin.buffer.read()
                if chars is not None:
                    data = data + chars
                timeout3 = timeout3 + 1
            data = data[:data.index(b'!') + 5]
            finished = True
        utime.sleep_ms(50)
        timeout = timeout + 1
    if timeout >= 10 and DEBUG:
        print("P1 Read timeout, skipping cycle")
        print("Read %s" % (str(data)))
        return None

    RTS(0)

    return data

def process_p1(data, first=False):
    if data is None:
        return

    crc = int(data[-4:], 16)

    md = memoryview(data)
    calc_crc = crc16(md[:-4])

    if DEBUG:
        print(data.decode())
    if ALWAYS_PUBLISH:
        first = True

    if crc != calc_crc:
        debug("Failed crc: %04X calculated %04X" % (crc, calc_crc))
        return

    global REPORTING_ATTRIBUTES
    global REPORTING_ATTRIBUTES2
    global RP_ENERGY_T1
    global RP_ENERGY_T2
    global RP_ENERGY_D_T1
    global RP_ENERGY_D_T2
    global RP_L1_A
    global RP_L1_V
    global RP_L1_P
    global RP_L2_A
    global RP_L2_V
    global RP_L2_P
    global RP_L3_A
    global RP_L3_V
    global RP_L3_P
    global RP_V_MUL
    global RP_V_DIV
    global RP_A_MUL
    global RP_A_DIV
    global RP_P_MUL
    global RP_P_DIV
    global RP_PHASES
    global RP_GAS
    REPORTING_ATTRIBUTES = []
    REPORTING_ATTRIBUTES2 = []

    phases = 0b001001
    # process data, we only look for specific types and ignore the rest
    for line in data.split(b"\r\n"):
        if b"1-0:1.8.1" in line: # energy in t1
            val = int(line[line.index(b"(") + 1: line.index(b"*")].replace(b".", b"")).to_bytes(6, 'little')
            if val != RP_ENERGY_T1[3] or first:
                RP_ENERGY_T1[3] = val
                REPORTING_ATTRIBUTES.append(RP_ENERGY_T1)
        elif b"1-0:1.8.2" in line: # energy in t2
            val = int(line[line.index(b"(") + 1: line.index(b"*")].replace(b".", b"")).to_bytes(6, 'little')
            if val != RP_ENERGY_T2[3] or first:
                RP_ENERGY_T2[3] = val
                REPORTING_ATTRIBUTES.append(RP_ENERGY_T2)
        elif b"1-0:2.8.1" in line: # energy from t1
            val = int(line[line.index(b"(") + 1: line.index(b"*")].replace(b".", b"")).to_bytes(6, 'little')
            if val != RP_ENERGY_D_T1[3] or first:
                RP_ENERGY_D_T1[3] = val
                REPORTING_ATTRIBUTES.append(RP_ENERGY_D_T1)
        elif b"1-0:2.8.2" in line: # energy from t2
            val = int(line[line.index(b"(") + 1: line.index(b"*")].replace(b".", b"")).to_bytes(6, 'little')
            if val != RP_ENERGY_D_T2[3] or first:
                RP_ENERGY_D_T2[3] = val
                REPORTING_ATTRIBUTES.append(RP_ENERGY_D_T2)
        elif b"1-0:1.7.0" in line: # Actual total power received from net
            pass
        elif b"1-0:2.7.0" in line: # Actual total power delivered to net
            pass
        elif b"1-0:31.7.0" in line: # amps from L1
            val = int(line[line.index(b"(") + 1: line.index(b"*")].replace(b".", b"")).to_bytes(2, 'little')
            if val != RP_L1_A[3] or first:
                RP_L1_A[3] = val
                REPORTING_ATTRIBUTES.append(RP_L1_A)
        elif b"1-0:51.7.0" in line: # amps from L2
            val = int(line[line.index(b"(") + 1: line.index(b"*")].replace(b".", b"")).to_bytes(2, 'little')
            phases |= 0b010000
            if val != RP_L2_A[3] or first:
                RP_L2_A[3] = val
                REPORTING_ATTRIBUTES.append(RP_L2_A)
        elif b"1-0:71.7.0" in line: # amps from L3
            val = int(line[line.index(b"(") + 1: line.index(b"*")].replace(b".", b"")).to_bytes(2, 'little')
            phases |= 0b100000
            if val != RP_L3_A[3] or first:
                RP_L3_A[3] = val
                REPORTING_ATTRIBUTES.append(RP_L3_A)
        elif b"1-0:32.7.0" in line: # volts from L1
            val = int(line[line.index(b"(") + 1: line.index(b"*")].replace(b".", b"")).to_bytes(2, 'little')
            if val != RP_L1_V[3] or first:
                RP_L1_V[3] = val
                REPORTING_ATTRIBUTES.append(RP_L1_V)
        elif b"1-0:52.7.0" in line: # volts from L2
            val = int(line[line.index(b"(") + 1: line.index(b"*")].replace(b".", b"")).to_bytes(2, 'little')
            phases |= 0b010000
            if val != RP_L2_V[3] or first:
                RP_L2_V[3] = val
                REPORTING_ATTRIBUTES.append(RP_L2_V)
        elif b"1-0:72.7.0" in line: # volts from L3
            val = int(line[line.index(b"(") + 1: line.index(b"*")].replace(b".", b"")).to_bytes(2, 'little')
            phases |= 0b100000
            if val != RP_L3_V[3] or first:
                RP_L3_V[3] = val
                REPORTING_ATTRIBUTES.append(RP_L3_V)
        elif b"1-0:21.7.0" in line: # POWER from L1
            val = int(line[line.index(b"(") + 1: line.index(b"*")].replace(b".", b"")).to_bytes(2, 'little')
            if val != RP_L1_P[3] or first:
                RP_L1_P[3] = val
                REPORTING_ATTRIBUTES.append(RP_L1_P)
        elif b"1-0:41.7.0" in line: # POWER from L2
            val = int(line[line.index(b"(") + 1: line.index(b"*")].replace(b".", b"")).to_bytes(2, 'little')
            phases |= 0b010000
            if val != RP_L2_P[3] or first:
                RP_L2_P[3] = val
                REPORTING_ATTRIBUTES.append(RP_L2_P)
        elif b"1-0:61.7.0" in line: # POWER from L3
            val = int(line[line.index(b"(") + 1: line.index(b"*")].replace(b".", b"")).to_bytes(2, 'little')
            phases |= 0b100000
            if val != RP_L3_P[3] or first:
                RP_L3_P[3] = val
                REPORTING_ATTRIBUTES.append(RP_L3_P)
        elif b"0-1:24.2.1" in line: # gas meter
            line2 = line[line.index(b"(") + 1:]
            val = int(line2[line2.index(b"(") + 1: line2.index(b"*")].replace(b".", b"")).to_bytes(6, 'little')
            if val != RP_GAS[3] or first:
                RP_GAS[3] = val
                REPORTING_ATTRIBUTES2.append(RP_GAS)

    phases = phases.to_bytes(4, 'little')
    if phases != RP_PHASES[3] or first or ALWAYS_PUBLISH:
        RP_PHASES[3] = phases
        REPORTING_ATTRIBUTES.append(RP_PHASES)
        REPORTING_ATTRIBUTES.append(RP_V_MUL)
        REPORTING_ATTRIBUTES.append(RP_V_DIV)
        REPORTING_ATTRIBUTES.append(RP_A_MUL)
        REPORTING_ATTRIBUTES.append(RP_A_DIV)
        REPORTING_ATTRIBUTES.append(RP_P_MUL)
        REPORTING_ATTRIBUTES.append(RP_P_DIV)

    if RP_L1_P[3] is not None or RP_L2_P[3] is not None or RP_L3_P[3] is not None:
        p1 = int.from_bytes(RP_L1_P[3], 'little') if RP_L1_P[3] is not None else 0
        p2 = int.from_bytes(RP_L2_P[3], 'little') if RP_L2_P[3] is not None else 0
        p3 = int.from_bytes(RP_L3_P[3], 'little') if RP_L3_P[3] is not None else 0
        RP_POWER_SUM[3] = int(p1 + p2 + p3).to_bytes(4, 'little')
        REPORTING_ATTRIBUTES.append(RP_POWER_SUM)

    if RP_ENERGY_T1[3] is not None or RP_ENERGY_T2[3] is not None:
        e1 = int.from_bytes(RP_ENERGY_T1[3], 'little') if RP_ENERGY_T1[3] is not None else 0
        e2 = int.from_bytes(RP_ENERGY_T2[3], 'little') if RP_ENERGY_T2[3] is not None else 0
        RP_ENERGY_SUM[3] = int(e1 + e2).to_bytes(6, 'little')
        REPORTING_ATTRIBUTES.append(RP_ENERGY_SUM)

    if first or ALWAYS_PUBLISH:
        REPORTING_ATTRIBUTES.append(RP_ENERGY_STATUS)
        REPORTING_ATTRIBUTES.append(RP_ENERGY_MUL)
        REPORTING_ATTRIBUTES.append(RP_ENERGY_DIV)
        REPORTING_ATTRIBUTES.append(RP_ENERGY_UOM)
        REPORTING_ATTRIBUTES2.append(RP_GAS_STATUS)
        REPORTING_ATTRIBUTES2.append(RP_GAS_MUL)
        REPORTING_ATTRIBUTES2.append(RP_GAS_DIV)
        REPORTING_ATTRIBUTES2.append(RP_GAS_UOM)

    if len(REPORTING_ATTRIBUTES) > 0:
        send_data()

timeout_counter = 0

while True:
    try:
        # If button 5 is pressed, drop to REPL
        if repl_button.value() == 0:
            led(0)
            print("Dropping to REPL")
            sys.exit()
        # Do nothing

        blink()
        if timeout_counter == CYCLE_TIME:
            try:
                data = read_p1()
            except Exception as e:
                print(e)
                print("Failed to read p1 port data")
                raise
            process_p1(data)

            #process_p1(TESTDATA, first)
            first = False
            timeout_counter = 0

        utime.sleep_ms(1000) # wait some time
        timeout_counter = timeout_counter + 1
    except Exception as e:
        print("Caught %s" % (str(e)))
        print(e)
        import machine
        machine.reset()
