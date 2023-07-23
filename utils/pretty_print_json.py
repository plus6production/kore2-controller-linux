import json

with open('display_packet_repr.json', 'r') as fp:
    data = json.load(fp)
    for packet in data:
        if 'data' in packet:
            print(*list(map(lambda val: hex(val), packet['data'])), sep=':')