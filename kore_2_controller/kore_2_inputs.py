# Handles buttons, encoders, scrub wheel
from utils import utils
from pubsub import pub

# TODO: Buttons can be rising edge, falling edge, or level

class Kore2Inputs:

    def __init__(self, usb_handler, debug=False):
        self.usb_handler = usb_handler
        self.debug = debug

        # Mapping of bits to functionality
        self.packet_byte_map = [
            {  # Byte 0 = menu buttons
                0 : 'f2',
                2 : 'control',
                3 : 'enter',
                4 : 'f1',
                5 : 'esc',
                6 : 'sound'
            },
            {  # Byte 1 = arrows and transport
                0 : 'right',
                1 : 'down',
                2 : 'up',
                3 : 'left',
                4 : 'listen',
                5 : 'record',
                6 : 'play',
                7 : 'stop'
            },
            {  # Byte 2 = silver function buttons
                3 : 'btn.1',
                2 : 'btn.2',
                1 : 'btn.3',
                0 : 'btn.4',
                4 : 'btn.5',
                5 : 'btn.6',
                6 : 'btn.7',
                7 : 'btn.8'
            },
            {  # Byte 3 = Knob touch sense
                6 : 'touch.1',
                4 : 'touch.2',
                2 : 'touch.3',
                0 : 'touch.4',
                7 : 'touch.5',
                5 : 'touch.6',
                3 : 'touch.7',
                1 : 'touch.8'
            }
        ]

        self.buttons = {
            'f2' :      { 'state' : False, '_is_pressed' : False, 'mode' : 'momentary' },
            'control' : { 'state' : False, '_is_pressed' : False, 'mode' : 'momentary' },
            'enter' :   { 'state' : False, '_is_pressed' : False, 'mode' : 'momentary' },
            'f1' :      { 'state' : False, '_is_pressed' : False, 'mode' : 'momentary' },
            'esc' :     { 'state' : False, '_is_pressed' : False, 'mode' : 'momentary' },
            'sound' :   { 'state' : False, '_is_pressed' : False, 'mode' : 'momentary' },
            'right' :   { 'state' : False, '_is_pressed' : False, 'mode' : 'momentary' },
            'down' :    { 'state' : False, '_is_pressed' : False, 'mode' : 'momentary' },
            'up' :      { 'state' : False, '_is_pressed' : False, 'mode' : 'momentary' },
            'left' :    { 'state' : False, '_is_pressed' : False, 'mode' : 'momentary' },
            'listen' :  { 'state' : False, '_is_pressed' : False, 'mode' : 'momentary' },
            'record' :  { 'state' : False, '_is_pressed' : False, 'mode' : 'momentary' },
            'play' :    { 'state' : False, '_is_pressed' : False, 'mode' : 'momentary' },
            'stop' :    { 'state' : False, '_is_pressed' : False, 'mode' : 'momentary' },
            'btn.1' :   { 'state' : False, '_is_pressed' : False, 'mode' : 'momentary' },
            'btn.2' :   { 'state' : False, '_is_pressed' : False, 'mode' : 'momentary' },
            'btn.3' :   { 'state' : False, '_is_pressed' : False, 'mode' : 'momentary' },
            'btn.4' :   { 'state' : False, '_is_pressed' : False, 'mode' : 'momentary' },
            'btn.5' :   { 'state' : False, '_is_pressed' : False, 'mode' : 'momentary' },
            'btn.6' :   { 'state' : False, '_is_pressed' : False, 'mode' : 'momentary' },
            'btn.7' :   { 'state' : False, '_is_pressed' : False, 'mode' : 'momentary' },
            'btn.8' :   { 'state' : False, '_is_pressed' : False, 'mode' : 'momentary' },
            'touch.1' : { 'state' : False, '_is_pressed' : False, 'mode' : 'momentary' },
            'touch.2' : { 'state' : False, '_is_pressed' : False, 'mode' : 'momentary' },
            'touch.3' : { 'state' : False, '_is_pressed' : False, 'mode' : 'momentary' },
            'touch.4' : { 'state' : False, '_is_pressed' : False, 'mode' : 'momentary' },
            'touch.5' : { 'state' : False, '_is_pressed' : False, 'mode' : 'momentary' },
            'touch.6' : { 'state' : False, '_is_pressed' : False, 'mode' : 'momentary' },
            'touch.7' : { 'state' : False, '_is_pressed' : False, 'mode' : 'momentary' },
            'touch.8' : { 'state' : False, '_is_pressed' : False, 'mode' : 'momentary' }
        }

        self.encoders = {
            'touch.1' : {},
            'touch.2' : {},
            'touch.3' : {},
            'touch.4' : {},
            'touch.5' : {},
            'touch.6' : {},
            'touch.7' : {},
            'touch.8' : {},
        }
    
    def publish_button_event(self, button_name, state):
        topic = 'controller.input.button.' + button_name
        pub.sendMessage(topic, arg1=topic, arg2=[state])

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
            self.publish_button_event(button_name, self.buttons[button_name]['state'])
        elif (is_pressed and self.buttons[button_name]['mode'] == 'rising') or (not is_pressed and self.buttons[button_name]['mode'] == 'falling'):
            self.buttons[button_name]['state'] = not self.buttons[button_name]['state']
            self.publish_button_event(button_name, self.buttons[button_name]['state'])

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
            self.check_button_for_state_change(key, is_pressed)


    # Handle opcode 0x4 data from Kore2Usb
    def handle_read_buttons(self, data):
        self.parse_io_buttons_state(list(data))
        # TODO: scrub wheel
    
    def handle_read_encoders(self, data):
        pass