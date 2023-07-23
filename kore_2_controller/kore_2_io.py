# Handles buttons, encoders, scrub wheel
from utils import utils

# TODO: Buttons can be rising edge, falling edge, or level

class Kore2Io:

    def __init__(self, usb_handler, debug=False):
        self.usb_handler = usb_handler
        self.debug = debug

        # Mapping of bits to functionality
        self.packet_byte_map = [
            {  # Byte 0 = menu buttons
                0 : 'F2',
                2 : 'CONTROL',
                3 : 'ENTER',
                4 : 'F1',
                5 : 'ESC',
                6 : 'SOUND'
            },
            {  # Byte 1 = arrows and transport
                0 : 'RIGHT',
                1 : 'DOWN',
                2 : 'UP',
                3 : 'LEFT',
                4 : 'LISTEN',
                5 : 'RECORD',
                6 : 'PLAY',
                7 : 'STOP'
            },
            {  # Byte 2 = silver function buttons
                3 : 'BTN_1',
                2 : 'BTN_2',
                1 : 'BTN_3',
                0 : 'BTN_4',
                4 : 'BTN_5',
                5 : 'BTN_6',
                6 : 'BTN_7',
                7 : 'BTN_8'
            },
            {  # Byte 3 = Knob touch sense
                6 : 'TOUCH_1',
                4 : 'TOUCH_2',
                2 : 'TOUCH_3',
                0 : 'TOUCH_4',
                7 : 'TOUCH_5',
                5 : 'TOUCH_6',
                3 : 'TOUCH_7',
                1 : 'TOUCH_8'
            }
        ]

        self.buttons = {
            'F2' :      { 'state' : False, '_is_pressed' : False, 'mode' : 'momentary', 'on_change' : self.default_on_change_callback },
            'CONTROL' : { 'state' : False, '_is_pressed' : False, 'mode' : 'momentary', 'on_change' : self.default_on_change_callback },
            'ENTER' :   { 'state' : False, '_is_pressed' : False, 'mode' : 'momentary', 'on_change' : self.default_on_change_callback },
            'F1' :      { 'state' : False, '_is_pressed' : False, 'mode' : 'momentary', 'on_change' : self.default_on_change_callback },
            'ESC' :     { 'state' : False, '_is_pressed' : False, 'mode' : 'momentary', 'on_change' : self.default_on_change_callback },
            'SOUND' :   { 'state' : False, '_is_pressed' : False, 'mode' : 'momentary', 'on_change' : self.default_on_change_callback },
            'RIGHT' :   { 'state' : False, '_is_pressed' : False, 'mode' : 'momentary', 'on_change' : self.default_on_change_callback },
            'DOWN' :    { 'state' : False, '_is_pressed' : False, 'mode' : 'momentary', 'on_change' : self.default_on_change_callback },
            'UP' :      { 'state' : False, '_is_pressed' : False, 'mode' : 'momentary', 'on_change' : self.default_on_change_callback },
            'LEFT' :    { 'state' : False, '_is_pressed' : False, 'mode' : 'momentary', 'on_change' : self.default_on_change_callback },
            'LISTEN' :  { 'state' : False, '_is_pressed' : False, 'mode' : 'momentary', 'on_change' : self.default_on_change_callback },
            'RECORD' :  { 'state' : False, '_is_pressed' : False, 'mode' : 'momentary', 'on_change' : self.default_on_change_callback },
            'PLAY' :    { 'state' : False, '_is_pressed' : False, 'mode' : 'momentary', 'on_change' : self.default_on_change_callback },
            'STOP' :    { 'state' : False, '_is_pressed' : False, 'mode' : 'momentary', 'on_change' : self.default_on_change_callback },
            'BTN_1' :   { 'state' : False, '_is_pressed' : False, 'mode' : 'rising', 'on_change' : self.default_on_change_callback },
            'BTN_2' :   { 'state' : False, '_is_pressed' : False, 'mode' : 'rising', 'on_change' : self.default_on_change_callback },
            'BTN_3' :   { 'state' : False, '_is_pressed' : False, 'mode' : 'rising', 'on_change' : self.default_on_change_callback },
            'BTN_4' :   { 'state' : False, '_is_pressed' : False, 'mode' : 'rising', 'on_change' : self.default_on_change_callback },
            'BTN_5' :   { 'state' : False, '_is_pressed' : False, 'mode' : 'rising', 'on_change' : self.default_on_change_callback },
            'BTN_6' :   { 'state' : False, '_is_pressed' : False, 'mode' : 'rising', 'on_change' : self.default_on_change_callback },
            'BTN_7' :   { 'state' : False, '_is_pressed' : False, 'mode' : 'rising', 'on_change' : self.default_on_change_callback },
            'BTN_8' :   { 'state' : False, '_is_pressed' : False, 'mode' : 'rising', 'on_change' : self.default_on_change_callback },
            'TOUCH_1' : { 'state' : False, '_is_pressed' : False, 'mode' : 'rising', 'on_change' : self.default_on_change_callback },
            'TOUCH_2' : { 'state' : False, '_is_pressed' : False, 'mode' : 'rising', 'on_change' : self.default_on_change_callback },
            'TOUCH_3' : { 'state' : False, '_is_pressed' : False, 'mode' : 'rising', 'on_change' : self.default_on_change_callback },
            'TOUCH_4' : { 'state' : False, '_is_pressed' : False, 'mode' : 'rising', 'on_change' : self.default_on_change_callback },
            'TOUCH_5' : { 'state' : False, '_is_pressed' : False, 'mode' : 'rising', 'on_change' : self.default_on_change_callback },
            'TOUCH_6' : { 'state' : False, '_is_pressed' : False, 'mode' : 'rising', 'on_change' : self.default_on_change_callback },
            'TOUCH_7' : { 'state' : False, '_is_pressed' : False, 'mode' : 'rising', 'on_change' : self.default_on_change_callback },
            'TOUCH_8' : { 'state' : False, '_is_pressed' : False, 'mode' : 'rising', 'on_change' : self.default_on_change_callback }
        }
    
    def default_on_change_callback(self, button_name):
        print(button_name, ":", self.buttons[button_name]['state'])

    def check_button_for_state_change(self, button_name, is_pressed):
        # Use the internal "_is_pressed" to keep track of raw button states

        # The controller sends state updates intermittently, which
        # messes with the toggle logic.
        # Avoid this by skipping state update logic if the internal
        # state hasn't changed
        if self.buttons[button_name]['_is_pressed'] == is_pressed:
            return

        self.buttons[button_name]['_is_pressed'] = is_pressed
        
        if self.buttons[button_name]['mode'] == 'momentary' and is_pressed != self.buttons[button_name]['state']:
            self.buttons[button_name]['state'] = is_pressed
            self.buttons[button_name]['on_change'](button_name)
        elif (is_pressed and self.buttons[button_name]['mode'] == 'rising') or (not is_pressed and self.buttons[button_name]['mode'] == 'falling'):
            self.buttons[button_name]['state'] = not self.buttons[button_name]['state']
            self.buttons[button_name]['on_change'](button_name)

    def scrub_callback(self, scrub_name, value):
        print(scrub_name, value)

    def parse_io_buttons_state(self, data):
        # Collect all the pressed buttons into one array
        pressed_buttons = []
        for index in range(4):
            status_byte = data[index]
            buttons = utils.get_bit_flag_indices(status_byte)
            pressed_buttons.extend(list(map(lambda bit: self.packet_byte_map[index][bit], buttons)))

        # TODO: the method of parsing buttons to an array that only contains PRESSED buttons seems
        # like an inefficiency, but I want to save optimization for later and I'm already here now.
        # So this TODO is a reminder for later to consider a more efficient way to handle this.
        for key in self.buttons:
            is_pressed = (key in pressed_buttons)
            if self.check_button_for_state_change(key, is_pressed):
                # Call the state change callback
                self.buttons[key]['on_change'](key, buttons[key]['state'])

    # Handle opcode 0x4 data from Kore2Usb
    def handle_read_io(self, data):
        self.parse_io_buttons_state(list(data))
        # TODO: scrub wheel
    
