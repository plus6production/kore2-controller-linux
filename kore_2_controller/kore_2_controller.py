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

        self.setup_callbacks()
    
    def initialize(self):
        self.usb_handler.start_handshake()
        self.display.initialize()
        self.usb_handler.finalize_handshake()
        # Turn on display LED
        self.leds.set_single_led('LCD', 40)

    def shutdown(self):
        self.usb_handler.close()

    def default_button_callback(self, button_name):
        if self.io.buttons[button_name]['state']:
            self.leds.set_single_led(button_name, 50)
        else:
            self.leds.set_single_led(button_name, 0)

    def setup_callbacks(self):
        self.usb_handler.set_io_message_callback(self.io.handle_read_io)
        # for btn in self.io.buttons:
        #     self.io.buttons[btn]['on_change'] = self.default_button_callback

    def handle_incoming_events(self, event):
        print("handle incoming")
        if event['context'] == 'track' and event['name'] == 'mute':
            if event['track'] != 'selected' and event['track'] != 'global':
                btn_name = 'BTN_' + str(event['track'])
                val = 0
                if event['args'][0]:
                    val = self.leds.MAX_LED_BRIGHTNESS
                self.leds.set_single_led(btn_name, val)