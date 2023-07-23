# Class to handle LED functionality

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
        self.led_map = {
            'F2' :      { 'index' : 28, 'brightness' : 0 },
            'CONTROL' : { 'index' : 26, 'brightness' : 0 },
            'ENTER' :   { 'index' : 24, 'brightness' : 0 },
            'F1' :      { 'index' : 27, 'brightness' : 0 },
            'ESC' :     { 'index' : 29, 'brightness' : 0 },
            'SOUND' :   { 'index' : 31, 'brightness' : 0 },
            'RIGHT' :   { 'index' : 22, 'brightness' : 0 },
            'DOWN' :    { 'index' : 20, 'brightness' : 0 },
            'UP' :      { 'index' : 16, 'brightness' : 0 },
            'LEFT' :    { 'index' : 18, 'brightness' : 0 },
            'LISTEN' :  { 'index' : 17, 'brightness' : 0 },
            'RECORD' :  { 'index' : 19, 'brightness' : 0 },
            'PLAY' :    { 'index' : 21, 'brightness' : 0 },
            'STOP' :    { 'index' : 23, 'brightness' : 0 },
            'BTN_1' :   { 'index' : 8,  'brightness' : 0 },
            'BTN_2' :   { 'index' : 12, 'brightness' : 0 },
            'BTN_3' :   { 'index' : 0,  'brightness' : 0 },
            'BTN_4' :   { 'index' : 4,  'brightness' : 0 },
            'BTN_5' :   { 'index' : 11, 'brightness' : 0 },
            'BTN_6' :   { 'index' : 15, 'brightness' : 0 },
            'BTN_7' :   { 'index' : 3,  'brightness' : 0 },
            'BTN_8' :   { 'index' : 7,  'brightness' : 0 },
            'TOUCH_1' : { 'index' : 10, 'brightness' : 0 },
            'TOUCH_2' : { 'index' : 14, 'brightness' : 0 },
            'TOUCH_3' : { 'index' : 2,  'brightness' : 0 },
            'TOUCH_4' : { 'index' : 6,  'brightness' : 0 },
            'TOUCH_5' : { 'index' : 9,  'brightness' : 0 },
            'TOUCH_6' : { 'index' : 13, 'brightness' : 0 },
            'TOUCH_7' : { 'index' : 1,  'brightness' : 0 },
            'TOUCH_8' : { 'index' : 5,  'brightness' : 0 },
            'LCD' :     { 'index' : 30, 'brightness' : 0 }
        }

        # Keep a byte array representation ready to send to the controller
        self.led_arr = bytearray(32)
    
    def send_controller_led_state(self):
        self.usb_handler.send_led_command(self.led_arr, 100)

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
