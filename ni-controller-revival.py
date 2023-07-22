import evdev
import asyncio

# Find "Kore controller 2"
kore2_name = 'Kore controller 2'
kore2_vid = 0x17cc
kore2_pid = 0x4712

kore2_device = None
device_found = False

# Mapping from event code to hardware
device_mapping = {
    evdev.ecodes.ecodes['BTN_1'] : ('f_btns', 0),
    evdev.ecodes.ecodes['BTN_2'] : ('f_btns', 1),
    evdev.ecodes.ecodes['BTN_3'] : ('f_btns', 2),
    evdev.ecodes.ecodes['BTN_4'] : ('f_btns', 3),
    evdev.ecodes.ecodes['BTN_5'] : ('f_btns', 7),
    evdev.ecodes.ecodes['BTN_6'] : ('f_btns', 6),
    evdev.ecodes.ecodes['BTN_7'] : ('f_btns', 5),
    evdev.ecodes.ecodes['BTN_8'] : ('f_btns', 4),
    evdev.ecodes.ecodes['ABS_HAT0X'] : ('knobs', 0),
    evdev.ecodes.ecodes['ABS_HAT0Y'] : ('knobs', 1),
    evdev.ecodes.ecodes['ABS_HAT1X'] : ('knobs', 2),
    evdev.ecodes.ecodes['ABS_HAT1Y'] : ('knobs', 3),
    evdev.ecodes.ecodes['ABS_HAT2X'] : ('knobs', 4),
    evdev.ecodes.ecodes['ABS_HAT2Y'] : ('knobs', 5),
    evdev.ecodes.ecodes['ABS_HAT3X'] : ('knobs', 6),
    evdev.ecodes.ecodes['ABS_HAT3Y'] : ('knobs', 7)
}

# State storage for device
k2_controller = {
    'knobs' : [0]*8,
    'f_btns' : [0]*8,
    'scrub' : 0
}

devices = [evdev.InputDevice(path) for path in evdev.list_devices()]

for device in devices:
    if device.info.vendor == kore2_vid and device.info.product == kore2_pid:
        kore2_device = device
        device_found = True

if not device_found:
    print("Unable to find Kore 2 controller, exiting")
    quit()

# Make us the only recipients of the events from the Kore 2 controller
kore2_device.grab()

def print_controller_state():
    knobs_printout = "Knobs: "
    for knob_val in k2_controller['knobs']:
        knobs_printout += str(knob_val) + ' '

    f_btns_printout = "F_Btns: "
    for btn_val in k2_controller['f_btns']:
        f_btns_printout += str(btn_val) + ' '

    print("Controller State:")
    print(knobs_printout)
    print(f_btns_printout)

def handle_key_event(event):
    print("keypress: ", event)

def handle_abs_event(event):
    print("abs: ", event)

def handle_syn_event(event):
    # I don't want to do anything with these
    pass

def event_handler(event):
    # Get properly typed event by using the event_factory?
    typed_event = evdev.util.categorize(event)
    #print(event.code, event.value)

    if event.code in device_mapping:
        group, index = device_mapping[event.code]
        k2_controller[group][index] = event.value
        print_controller_state()

    '''
    if event.type == evdev.ecodes.EV_KEY:
        handle_key_event(event)
    elif event.type == evdev.ecodes.EV_ABS:
        handle_abs_event(event)
    elif event.type == evdev.ecodes.EV_SYN:
        handle_syn_event(event)
    else:
        print("Unhandled ev code: ", event.type)
    '''


async def helper(dev):
    async for ev in dev.async_read_loop():
        event_handler(ev)

loop = asyncio.get_event_loop()
loop.run_until_complete(helper(kore2_device))
