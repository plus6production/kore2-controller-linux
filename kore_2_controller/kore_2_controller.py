from kore_2_controller.kore_2_usb import Kore2USB
from kore_2_controller.kore_2_display import Kore2Display
from kore_2_controller.kore_2_leds import Kore2Leds
from kore_2_controller.kore_2_io import Kore2Io

# Top-level container class for managing/accessing Kore 2 controller functionality

class Kore2Controller:
    def __init__(self, debug=False):
        self.placeholder = True
        self.usb_handler = Kore2USB(debug)
        self.usb_handler.open()
        self.display = Kore2Display(self.usb_handler, debug)
        self.leds = Kore2Leds(self.usb_handler, debug)
        self.io = Kore2Io(self.usb_handler, debug)

        self.usb_handler.set_io_message_callback(self.io.handle_read_io)
    
    def initialize(self):
        self.usb_handler.start_handshake()
        self.display.initialize()
        self.usb_handler.finalize_handshake()
        # Turn on display LED
        self.leds.set_single_led(30, 40)

    def shutdown(self):
        self.usb_handler.close()