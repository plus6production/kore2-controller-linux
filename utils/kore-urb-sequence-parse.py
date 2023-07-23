import json

EZUSB_CPUCS_REG = 0xe600
FIRMWARE_DOWNLOAD_REQUEST_TYPE = 0x40
FIRMWARE_DOWNLOAD_REQUEST = 0xA0
# The other data needed is the target memory address (which goes in wValue),
# the data length (in wLength) and the actual data buffer

# Note: the endpoint number gives us the direction, if 1 << 8 is set, direction is in

transfer_types = {
    0x02 : 'URB_CONTROL',

}

startup_sequence = []
display_sequence = []

def convert_json_string_to_bytearray(json_string):
    if json_string is None:
            return []
    int_arr = list(map(lambda x: int(x, base=16), json_string.split(':')))
    return int_arr

def create_control_packet_repr(packet):
    packet_repr = {
        'transfer_type' : int(packet['_source']['layers']['usb']['usb.transfer_type'], base=16),
        'endpoint' : int(packet['_source']['layers']['usb']['usb.endpoint_address'], base=16),
        'request_type' : int(packet['_source']['layers']['Setup Data']['usb.bmRequestType'], base=16),
        'request' : int(packet['_source']['layers']['Setup Data']['usb.setup.bRequest']),
        'value' : int(packet['_source']['layers']['Setup Data'].get('usb.setup.wValue', '0'), base=16),
        'length' : int(packet['_source']['layers']['Setup Data']['usb.setup.wLength']),
        'data' : convert_json_string_to_bytearray(packet['_source']['layers']['Setup Data'].get('usb.data_fragment', None))
    }
    return packet_repr

def create_bulk_packet_repr(packet):
    packet_repr = {
        'transfer_type' : int(packet['_source']['layers']['usb']['usb.transfer_type'], base=16),
        'endpoint' : int(packet['_source']['layers']['usb']['usb.endpoint_address'], base=16),
        'length' : int(packet['_source']['layers']['usb']['usb.data_len']),
        'data' : convert_json_string_to_bytearray(packet['_source']['layers'].get('usb.capdata', None))
    }
    return packet_repr

def create_packet_representation(packet):
    if int(packet['_source']['layers']['usb']['usb.transfer_type'], base=16) == 0x02:
        return create_control_packet_repr(packet)
    elif int(packet['_source']['layers']['usb']['usb.transfer_type'], base=16) == 0x03:
        return create_bulk_packet_repr(packet)
    return {}

'''
def print_useful_packet_data(packet, outfile):

    output_string = 'Frame: ' + packet['_source']['layers']['frame']['frame.number']
    output_string += ' EP: ' +  packet['_source']['layers']['usb']['usb.endpoint_address']    
    #output_string += ' Desc_Idx: ' + packet['_source']['layers']['Setup Data'].get('usb.DescriptorIndex', 'NONE')
    #output_string += ' Desc_Type: ' + packet['_source']['layers']['Setup Data'].get('usb.bDescriptorType', 'NONE')
    output_string += ' Req_Type: ' + packet['_source']['layers']['Setup Data']['usb.bmRequestType']
    output_string += ' Req: ' + packet['_source']['layers']['Setup Data']['usb.setup.bRequest']
    output_string += ' Value: ' + packet['_source']['layers']['Setup Data'].get('usb.setup.wValue', "NONE")
    output_string += ' Length: ' + packet['_source']['layers']['Setup Data']['usb.setup.wLength']
    output_string += ' Index: ' + packet['_source']['layers']['Setup Data']['usb.setup.wIndex']

    # if 'usb.data_fragment' in packet['_source']['layers']['Setup Data']:
    #     fragment = packet['_source']['layers']['Setup Data']['usb.data_fragment']
    #     int_arr = list(map(lambda x: int(x, base=16), fragment.split(':')))
    #     print(int_arr)

    # 264
    # 1120

    output_string += ' Data_Frag: ' + packet['_source']['layers']['Setup Data'].get('usb.data_fragment', 'NO DATA')

    if 'usb.data_fragment' in packet['_source']['layers']['Setup Data']:
        #print(type(packet['_source']['layers']['Setup Data']['usb.data_fragment']))
        buffer_str = packet['_source']['layers']['Setup Data']['usb.data_fragment']
        int_arr = list(map(lambda x: int(x, base=16), buffer_str.split(':')))
        byte_arr = bytearray(int_arr)
        # print(byte_arr)
        outfile.write(bytes(byte_arr))

    print(output_string)
    return int(packet['_source']['layers']['Setup Data']['usb.setup.wLength'])
'''

data = json.load(fp=open('usb_capture_data/Kore_Initial_Display_Setup_After_Reset.json', 'r'))
#print(data)

formatted_data = json.dumps(data, indent=2)
print(formatted_data)

data_len = 0
#bin_file = open('firmware_data.bin', 'wb')
#bin_file = None
#for packet in data[11:-3]:

for packet in data:    
    #startup_sequence.append(create_packet_representation(packet))
    display_sequence.append(create_packet_representation(packet))

with open('display_packet_repr.json', 'w') as fd:
    #json.dump(startup_sequence, fd)
    json.dump(display_sequence, fd)

print(display_sequence)

#bin_file.close()


