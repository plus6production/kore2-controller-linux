# Class to handle LED functionality
from pubsub import pub
from utils import utils

'''
static const struct caiaq_controller kore_controller[] = {
	{ "LED F1",		8   | CNT_INTVAL },
	{ "LED F2",		12  | CNT_INTVAL },
	{ "LED F3",		0   | CNT_INTVAL },
	{ "LED F4",		4   | CNT_INTVAL },
	{ "LED F5",		11  | CNT_INTVAL },
	{ "LED F6",		15  | CNT_INTVAL },
	{ "LED F7",		3   | CNT_INTVAL },
	{ "LED F8",		7   | CNT_INTVAL },
	{ "LED touch1",	     	10  | CNT_INTVAL },
	{ "LED touch2",	     	14  | CNT_INTVAL },
	{ "LED touch3",	     	2   | CNT_INTVAL },
	{ "LED touch4",	     	6   | CNT_INTVAL },
	{ "LED touch5",	     	9   | CNT_INTVAL },
	{ "LED touch6",	     	13  | CNT_INTVAL },
	{ "LED touch7",	     	1   | CNT_INTVAL },
	{ "LED touch8",	     	5   | CNT_INTVAL },
	{ "LED left",	       	18  | CNT_INTVAL },
	{ "LED right",	     	22  | CNT_INTVAL },
	{ "LED up",		16  | CNT_INTVAL },
	{ "LED down",	       	20  | CNT_INTVAL },
	{ "LED stop",	       	23  | CNT_INTVAL },
	{ "LED play",	       	21  | CNT_INTVAL },
	{ "LED record",	     	19  | CNT_INTVAL },
	{ "LED listen",		17  | CNT_INTVAL },
	{ "LED lcd",		30  | CNT_INTVAL },
	{ "LED menu",		28  | CNT_INTVAL },
	{ "LED sound",	 	31  | CNT_INTVAL },
	{ "LED esc",		29  | CNT_INTVAL },
	{ "LED view",		27  | CNT_INTVAL },
	{ "LED enter",		24  | CNT_INTVAL },
	{ "LED control",	26  | CNT_INTVAL }
}
'''

class Kore2Leds:
    def __init__(self, usb_handler, debug=False):
        self.debug = debug
        self.usb_handler = usb_handler
        self.MAX_LED_BRIGHTNESS = 63

        self.listeners = set()
        self.listeners.add(pub.subscribe(self.handle_led_topic, 'controller.output.led'))

        # TODO: Update to lowercase and dot based for pubsub
        self.led_map = {
            'f2' :      { 'index' : 28, 'brightness' : 0 },
            'control' : { 'index' : 26, 'brightness' : 0 },
            'enter' :   { 'index' : 24, 'brightness' : 0 },
            'f1' :      { 'index' : 27, 'brightness' : 0 },
            'esc' :     { 'index' : 29, 'brightness' : 0 },
            'sound' :   { 'index' : 31, 'brightness' : 0 },
            'right' :   { 'index' : 22, 'brightness' : 0 },
            'down' :    { 'index' : 20, 'brightness' : 0 },
            'up' :      { 'index' : 16, 'brightness' : 0 },
            'left' :    { 'index' : 18, 'brightness' : 0 },
            'listen' :  { 'index' : 17, 'brightness' : 0 },
            'record' :  { 'index' : 19, 'brightness' : 0 },
            'play' :    { 'index' : 21, 'brightness' : 0 },
            'stop' :    { 'index' : 23, 'brightness' : 0 },
            'btn.1' :   { 'index' : 8,  'brightness' : 0 },
            'btn.2' :   { 'index' : 12, 'brightness' : 0 },
            'btn.3' :   { 'index' : 0,  'brightness' : 0 },
            'btn.4' :   { 'index' : 4,  'brightness' : 0 },
            'btn.5' :   { 'index' : 11, 'brightness' : 0 },
            'btn.6' :   { 'index' : 15, 'brightness' : 0 },
            'btn.7' :   { 'index' : 3,  'brightness' : 0 },
            'btn.8' :   { 'index' : 7,  'brightness' : 0 },
            'touch.1' : { 'index' : 10, 'brightness' : 0 },
            'touch.2' : { 'index' : 14, 'brightness' : 0 },
            'touch.3' : { 'index' : 2,  'brightness' : 0 },
            'touch.4' : { 'index' : 6,  'brightness' : 0 },
            'touch.5' : { 'index' : 9,  'brightness' : 0 },
            'touch.6' : { 'index' : 13, 'brightness' : 0 },
            'touch.7' : { 'index' : 1,  'brightness' : 0 },
            'touch.8' : { 'index' : 5,  'brightness' : 0 },
            'lcd' :     { 'index' : 30, 'brightness' : 0 }
        }

        # Keep a byte array representation ready to send to the controller
        self.led_arr = bytearray(32)
    
    def send_controller_led_state(self):
        self.usb_handler.send_led_command(self.led_arr, 100)

    def handle_led_topic(self, arg1, arg2):
        #print("handle_led_topic:", arg1, arg2)
        split = utils.split_and_strip_topic_to_list(arg1, 3)
        led_name = ''
        if len(split) == 2:
            if split[0] == 'touch' or split[0] == 'btn':
                led_name = split[0] + '.' + split[1]
        elif len(split) == 1:
            led_name = split[0]
        else:
            return

        val = 0
        if len(arg2) == 1:
            val = int(arg2[0])
            # TODO: better override for boolean inputs
            # This should be handled in the "model" by providing a type or a min/max
            if split[0] == 'btn' and val == 1:
                val = 1024
        if val > 0:
            val = utils.convert_val_between_ranges(val, (0, 1024), (0, 63))
     
        self.set_single_led(led_name, val)    

    # Test function that sets a single LED while clearing the others
    def set_single_led(self, name, value):
        # Bounds
        if value < 0:
            value = 0       
        elif value > 63:
            value = 63

        self.led_map[name]['brightness'] = value
        self.led_arr[self.led_map[name]['index']] = value
        self.send_controller_led_state()
    
    def set_leds(self, name_value_pairs):
        pass
