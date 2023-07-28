from kore_2_controller.kore_2_usb import Kore2USB
from kore_2_controller.kore_2_display import Kore2Display
from kore_2_controller.kore_2_leds import Kore2Leds
from kore_2_controller.kore_2_inputs import Kore2Inputs
from kore_2_controller.kore_2_midi import Kore2Midi
from kore_2_controller.contexts.mixer import MixerContext
from pubsub import pub
from utils import utils

# Top-level container class for managing/accessing Kore 2 controller functionality

class Kore2Controller:
    def __init__(self, debug=False):
        self.placeholder = True
        self.usb_handler = Kore2USB(debug)
        self.usb_handler.open()
        self.display = Kore2Display(self.usb_handler, debug)
        self.leds = Kore2Leds(self.usb_handler, debug)
        self.input = Kore2Inputs(self.usb_handler, debug)
        self.midi = Kore2Midi(self.usb_handler, debug)
        self.setup_callbacks()
        self.listeners = set()
        self.current_context = None
    
    def initialize(self):
        self.usb_handler.start_handshake()
        self.display.initialize()
        self.usb_handler.finalize_handshake()
        # Turn on display LED
        self.leds.set_single_led('lcd', 40)

        self.midi.connect()

        self.current_context = MixerContext(self.display.enqueue_frame, tick_rate=0.2)
        self.current_context.activate_context()

    def shutdown(self):
        self.current_context.deactivate_context()
        self.midi.disconnect()
        self.display.shutdown()
        self.usb_handler.close()

    def default_button_callback(self, button_name):
        if self.input.buttons[button_name]['state']:
            self.leds.set_single_led(button_name, 50)
        else:
            self.leds.set_single_led(button_name, 0)

    def setup_callbacks(self):
        self.usb_handler.set_button_opcode_callback(self.input.handle_read_buttons)
        self.usb_handler.set_encoder_opcode_callback(self.input.handle_read_encoders)
        self.usb_handler.set_midi_read_callback(self.midi.handle_midi_bytes_from_controller)
