# Handles buttons, encoders, scrub wheel
from utils import utils
from pubsub import pub
import numpy

# TODO: Buttons can be rising edge, falling edge, or level

class Kore2Inputs:

    def __init__(self, usb_handler, debug=False):
        self.usb_handler = usb_handler
        self.debug = debug
        self.encoder_counts_per_rev = 512
        self.encoder_lines_per_rev = 2
        self.is_cw_positive = True

        # Mapping of bits to functionality
        self.button_packet_byte_map = [
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

        # Right now the encoders could be infinite (absolute) or bounded (abs + offset)
        # The presence of min/max indicates bounded - max is inclusive
        self.encoders = [
            { '_packet_indices' : [7, 5],   'value' : 0, '_scaled' : 0, 'min' : 0, 'max' : 1023, '_offset' : 0, '_raw_ab' : [0, 0], '_line_count' : 0, '_phase' : 0, '_course_radians' : 0, '_fine_radians' : 0 },
            { '_packet_indices' : [12, 14], 'value' : 0, '_scaled' : 0, 'min' : 0, 'max' : 1023, '_offset' : 0, '_raw_ab' : [0, 0], '_line_count' : 0, '_phase' : 0, '_course_radians' : 0, '_fine_radians' : 0 },
            { '_packet_indices' : [15, 13], 'value' : 0, '_scaled' : 0, 'min' : 0, 'max' : 1023, '_offset' : 0, '_raw_ab' : [0, 0], '_line_count' : 0, '_phase' : 0, '_course_radians' : 0, '_fine_radians' : 0 },
            { '_packet_indices' : [0, 2],   'value' : 0, '_scaled' : 0, 'min' : 0, 'max' : 1023, '_offset' : 0, '_raw_ab' : [0, 0], '_line_count' : 0, '_phase' : 0, '_course_radians' : 0, '_fine_radians' : 0 },
            { '_packet_indices' : [3, 1],   'value' : 0, '_scaled' : 0, 'min' : 0, 'max' : 1023, '_offset' : 0, '_raw_ab' : [0, 0], '_line_count' : 0, '_phase' : 0, '_course_radians' : 0, '_fine_radians' : 0 },
            { '_packet_indices' : [8, 10],  'value' : 0, '_scaled' : 0, 'min' : 0, 'max' : 1023, '_offset' : 0, '_raw_ab' : [0, 0], '_line_count' : 0, '_phase' : 0, '_course_radians' : 0, '_fine_radians' : 0 },
            { '_packet_indices' : [11, 9],  'value' : 0, '_scaled' : 0, 'min' : 0, 'max' : 1023, '_offset' : 0, '_raw_ab' : [0, 0], '_line_count' : 0, '_phase' : 0, '_course_radians' : 0, '_fine_radians' : 0 },
            { '_packet_indices' : [4, 6],   'value' : 0, '_scaled' : 0, 'min' : 0, 'max' : 1023, '_offset' : 0, '_raw_ab' : [0, 0], '_line_count' : 0, '_phase' : 0, '_course_radians' : 0, '_fine_radians' : 0 },
        ]
    
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
            pressed_buttons.extend(list(map(lambda bit: self.button_packet_byte_map[index][bit], buttons)))

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

    def calculate_interpolated_encoder_value(self, encoder, new_raw_ab):
        line_count = encoder['_line_count']
        course_radians = line_count * (numpy.pi/2)
        raw_offset = -128
        b_crossing_threshold = 0.5

        a1_scaled = (new_raw_ab[0] + raw_offset)
        a1_sign = numpy.sign(a1_scaled)
        b1_scaled = (new_raw_ab[1] + raw_offset)
        b1_sign = numpy.sign(b1_scaled)

        last_phase = encoder['_phase']
        last_phase_sign = numpy.sign(last_phase)

        # get signal phase:
        phase = 0
        if b1_scaled == 0:
            phase = (numpy.pi * a1_sign * b1_sign) - numpy.pi/2
        else:
            phase = numpy.arctan(a1_scaled/b1_scaled)

        phase_sign = numpy.sign(phase)

        #print('phase:', phase)
        encoder['_phase'] = phase

        # did phase cross zero?
        # we only really care if it was a 'B' (cos) crossing,
        # which is a large jump from -pi/2 to pi/2 or vise versa
        if last_phase_sign != phase_sign:
            # phase switched sign, check if a B crossing has occurred
            if abs(phase - last_phase) > b_crossing_threshold:
                # B crossing has occured, which direction?
                if phase > 0:
                    # CW crossing
                    encoder['_line_count'] -= 1
                elif phase < 0:
                    encoder['_line_count'] += 1
                else: # at a B crossing, phase should NEVER be zero, so no magic logic here
                    print("PHASE ZERO AT CROSSING, SHOULDN'T HAPPEN")
                
                encoder['_course_radians'] = encoder['_line_count'] * ((2*numpy.pi) / self.encoder_lines_per_rev)

        # Offset so fine measurement is never negative
        encoder['_fine_radians'] = phase + numpy.pi / 2
        encoder['_scaled']  = int((encoder['_course_radians'] + encoder['_fine_radians']) * (self.encoder_counts_per_rev / (2*numpy.pi)))
        if self.is_cw_positive:
            encoder['_scaled'] *= -1

    # note: index_z is zero-based, but the topics/osc are 1-based indexing
    def publish_encoder_event(self, index_z, val):
        topic = 'controller.input.encoder.' + str(index_z + 1)
        pub.sendMessage(topic, arg1=topic, arg2=[val])

    def handle_read_encoders(self, data):
        truncated_data = list(data)[:16]
        rollover_threshold = 200
        zero_offset = -128
        #print("encoders raw:", truncated_data)

        for encoder_index in range(len(self.encoders)):
            encoder = self.encoders[encoder_index]
            last_val = encoder['_raw_ab']
            indices = encoder['_packet_indices']
            current_val = [truncated_data[indices[0]], truncated_data[indices[1]]]
            if last_val[0] != current_val[0] or last_val[1] != current_val[1]:
                self.calculate_interpolated_encoder_value(encoder, current_val)
                encoder['_raw_ab'] = current_val

                if 'max' in encoder and (encoder['_scaled'] - encoder['_offset']) > encoder['max']:
                    encoder['_offset'] = encoder['_scaled'] - encoder['max']
                
                if 'min' in encoder and (encoder['_scaled'] - encoder['_offset']) < encoder['min']:
                    encoder['_offset'] = encoder['_scaled']
                
                # TODO: handle min/max at a higher level, since that is application-dependent
                last_val = encoder['value']
                encoder['value'] = encoder['_scaled'] - encoder['_offset']
                #if encoder_index == 0:
                    #print('val:', encoder['value'], 'unbounded:', encoder['_scaled'], 'course:', encoder['_course_radians'], 'fine:', encoder['_fine_radians'], 'lines:', encoder['_line_count'])
                
                # If the scaled and bounded value has changed, publish
                if last_val != encoder['value']:
                    self.publish_encoder_event(encoder_index, encoder['value'])






