from time import sleep
from pyalsa import alsacard, alsamixer, alsahcontrol

'''
print('interface_id:')
print('  ', alsahcontrol.interface_id)
print('interface_name:')
print('  ', alsahcontrol.interface_name)
print('element_type:')
print('  ', alsahcontrol.element_type)
print('element_type_name:')
print('  ', alsahcontrol.element_type_name)
print('event_class:')
print('  ', alsahcontrol.event_class)
print('event_mask:')
print('  ', alsahcontrol.event_mask)
print('event_mask_remove:', alsahcontrol.event_mask_remove)
print('  ', alsahcontrol.open_mode)
print('event_mask_remove:', alsahcontrol.open_mode)
'''

controller_name = 'Kore controller 2'
controller_index = -1

'''
caiaq driver mapping that will be parsed into id_map:
1 LED F1
2 LED F2
3 LED F3
4 LED F4
5 LED F5
6 LED F6
7 LED F7
8 LED F8
31 LED control
20 LED down
30 LED enter
28 LED esc
25 LED lcd
17 LED left
24 LED listen
26 LED menu
22 LED play
23 LED record
18 LED right
27 LED sound
21 LED stop
9 LED touch1
10 LED touch2
11 LED touch3
12 LED touch4
13 LED touch5
14 LED touch6
15 LED touch7
16 LED touch8
19 LED up
29 LED view
'''

id_map = {}

def generate_id_map(hctl):
    ctl_list = hctl.list()
    for ctl in ctl_list:
        id_map[ctl[4]] = ctl[0]


def set_control(hctl, name, value):
    element = alsahcontrol.Element(hctl, id_map[name])
    info = alsahcontrol.Info(element)
    hw_val = alsahcontrol.Value(element)
    hw_val.set_array(info.type, [value])
    hw_val.write()

# Get card list (just a list of indices because wut?)
card_numbers = alsacard.card_list()
for card_number in card_numbers:
    if controller_name in alsacard.card_get_name(card_number):
        controller_index = card_number
        break

print("index ", controller_index)

hctl = alsahcontrol.HControl(name='hw:%d'%(controller_index))

ctl_list = hctl.list()
for ctl in ctl_list:
    print(ctl[0], ctl[4])

generate_id_map(hctl)

for val in range(64):
    set_control(hctl, 'LED touch1', val)
    sleep(0.2)

for val in range(64):
    set_control(hctl, 'LED touch1', 63 - val)
    sleep(0.2)


