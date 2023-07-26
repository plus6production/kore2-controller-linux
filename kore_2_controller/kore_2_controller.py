from kore_2_controller.kore_2_usb import Kore2USB
from kore_2_controller.kore_2_display import Kore2Display
from kore_2_controller.kore_2_leds import Kore2Leds
from kore_2_controller.kore_2_inputs import Kore2Inputs
from models.mixer import MixerModel
from pubsub import pub

# Top-level container class for managing/accessing Kore 2 controller functionality

class Kore2Controller:
    def __init__(self, debug=False):
        self.placeholder = True
        self.usb_handler = Kore2USB(debug)
        self.usb_handler.open()
        self.display = Kore2Display(self.usb_handler, debug)
        self.leds = Kore2Leds(self.usb_handler, debug)
        self.input = Kore2Inputs(self.usb_handler, debug)
        self.setup_callbacks()
        self.listeners = set()
        self.current_context = None
    
    def initialize(self):
        self.usb_handler.start_handshake()
        self.display.initialize()
        self.usb_handler.finalize_handshake()
        # Turn on display LED
        self.leds.set_single_led('LCD', 40)

        self.listeners.add(pub.subscribe(self.handle_track_event, 'daw.from.track'))
        self.listeners.add(pub.subscribe(self.handle_button_event, 'controller.input.button'))
        self.listeners.add(pub.subscribe(self.handle_encoder_event, 'controller.input.encoder'))

        self.current_context = MixerModel()

    def shutdown(self):
        self.usb_handler.close()

    def default_button_callback(self, button_name):
        if self.input.buttons[button_name]['state']:
            self.leds.set_single_led(button_name, 50)
        else:
            self.leds.set_single_led(button_name, 0)

    def setup_callbacks(self):
        self.usb_handler.set_button_opcode_callback(self.input.handle_read_buttons)
        self.usb_handler.set_encoder_opcode_callback(self.input.handle_read_encoders)

    # Splits the provided topic string into its parts and
    # removes the specified number of leading parts
    def split_and_strip_topic_to_list(self, topic, num_prefixes=0):
        return topic.split('.')[num_prefixes:]

    def handle_daw_from_sub(self, arg1, arg2):
        # arg1 is the pubsub topic
        # arg2 is the actual args
        addr_list = split_topic_to_list(arg1)

    def handle_track_event(self, arg1, arg2):
        #print("sub: handle_track_event")
        #print(arg1)
        #print(arg2)
        addr_list = self.split_and_strip_topic_to_list(arg1, 3)
        if addr_list[0].isnumeric():
            if addr_list[1] == 'mute':
                btn_name = 'BTN_' + addr_list[0]
                val = 0
                if arg2[0]:
                    val = self.leds.MAX_LED_BRIGHTNESS
                self.leds.set_single_led(btn_name, val)
    
    def handle_button_event(self, arg1, arg2):
        if self.current_context is not None:
            if len(arg2) > 0 and arg2[0] == True:
                #print("Kore2Controller: handle_button_event PRESS")
                if arg1 in self.current_context.input_to_daw_mapping:
                    #print("sending event to topic", self.current_context.input_to_daw_mapping[arg1])
                    pub.sendMessage(self.current_context.input_to_daw_mapping[arg1], arg1=self.current_context.input_to_daw_mapping[arg1], arg2=[])
    
    def handle_encoder_event(self, arg1, arg2):
        if self.current_context is not None:
            if arg1 in self.current_context.input_to_daw_mapping:
                pub.sendMessage(self.current_context.input_to_daw_mapping[arg1], arg1=self.current_context.input_to_daw_mapping[arg1], arg2=arg2)