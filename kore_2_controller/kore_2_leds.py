# Class to handle LED functionality

class Kore2Leds:
    def __init__(self, usb_handler, debug=False):
        self.debug = debug
        self.usb_handler = usb_handler
    
    # Test function that sets a single LED while clearing the others
    def set_single_led(self, index, value):
        data = bytearray(64)
        data[index] = value
        self.usb_handler.send_led_command(data, 100)