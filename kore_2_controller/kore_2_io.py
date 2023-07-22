# Handles buttons, encoders, scrub wheel
from utils import utils

class Kore2Io:

    def __init__(self, usb_handler, debug=False):
        self.usb_handler = usb_handler
        self.debug = debug
            # Mapping of bits to functionality
        self.menu_button_bit_map = {
            0 : 'F2',
            2 : 'CONTROL',
            3 : 'ENTER',
            4 : 'F1',
            5 : 'ESC',
            6 : 'SOUND'
        }

        self.nav_transport_bit_map = {
            0 : 'RIGHT',
            1 : 'DOWN',
            2 : 'UP',
            3 : 'LEFT',
            4 : 'LISTEN',
            5 : 'RECORD',
            6 : 'PLAY',
            7 : 'STOP'
        }

        self.silver_button_bit_map = {
            3 : 'BTN_1',
            2 : 'BTN_2',
            1 : 'BTN_3',
            0 : 'BTN_4',
            4 : 'BTN_5',
            5 : 'BTN_6',
            6 : 'BTN_7',
            7 : 'BTN_8'
        }

        self.touch_sense_bit_map = {
            6 : 'TOUCH_1',
            4 : 'TOUCH_2',
            2 : 'TOUCH_3',
            0 : 'TOUCH_4',
            7 : 'TOUCH_5',
            5 : 'TOUCH_6',
            3 : 'TOUCH_7',
            1 : 'TOUCH_8'
        }

        self.button_states = {

        }

        # TODO: "on" and "off" callbacks
        self.button_callbacks = {
            'F2' : self.default_button_callback,
            'CONTROL' : self.default_button_callback,
            'ENTER' : self.default_button_callback,
            'F1' : self.default_button_callback,
            'ESC' : self.default_button_callback,
            'SOUND' : self.default_button_callback,
            'RIGHT' : self.default_button_callback,
            'DOWN' : self.default_button_callback,
            'UP' : self.default_button_callback,
            'LEFT' : self.default_button_callback,
            'LISTEN' : self.default_button_callback,
            'RECORD' : self.default_button_callback,
            'PLAY' : self.default_button_callback,
            'STOP' : self.default_button_callback,
            'BTN_1' : self.default_button_callback,
            'BTN_2' : self.default_button_callback,
            'BTN_3' : self.default_button_callback,
            'BTN_4' : self.default_button_callback,
            'BTN_5' : self.default_button_callback,
            'BTN_6' : self.default_button_callback,
            'BTN_7' : self.default_button_callback,
            'BTN_8' : self.default_button_callback,
            'TOUCH_1' : self.default_button_callback,
            'TOUCH_2' : self.default_button_callback,
            'TOUCH_3' : self.default_button_callback,
            'TOUCH_4' : self.default_button_callback,
            'TOUCH_5' : self.default_button_callback,
            'TOUCH_6' : self.default_button_callback,
            'TOUCH_7' : self.default_button_callback,
            'TOUCH_8' : self.default_button_callback
        }
    
    def default_button_callback(self, button_name, is_pressed):
        print(button_name, is_pressed)

    def scrub_callback(self, scrub_name, value):
        print(scrub_name, value)

    # Handle opcode 0x4 data from Kore2Usb
    # TODO: detect on and off state changes and store state instead of just printing
    def handle_read_io(self, data):
        utils.print_to_file("handle_read_io:", list(data))
        self.parse_print_io_byte(data[0], self.menu_button_bit_map, 'Menu Buttons')
        self.parse_print_io_byte(data[1], self.nav_transport_bit_map, 'Transport/Nav Buttons')
        self.parse_print_io_byte(data[2], self.silver_button_bit_map, "Silver Buttons")
        self.parse_print_io_byte(data[3], self.touch_sense_bit_map, "Touch-sense")
    
    def parse_print_io_byte(self, status_byte, bit_mapping, label):
        buttons = utils.get_bit_flag_indices(status_byte)
        #print("parse_print_io_byte: indices", buttons)
        mapped_buttons = list(map(lambda bit: bit_mapping[bit], buttons))
        for btn in mapped_buttons:
            if btn in self.button_callbacks:
                self.button_callbacks[btn](btn, True)
        mapped_buttons.sort()
        #print(mapped_buttons)
        #utils.print_to_file(label, mapped_buttons)
