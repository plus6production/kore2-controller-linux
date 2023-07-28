import mido
import rtmidi
from queue import SimpleQueue
import threading

class Kore2Midi:
    def __init__(self, usb_handler, debug=False):
        self.usb_handler = usb_handler
        self.midi_in= rtmidi.MidiIn(rtapi=rtmidi.API_LINUX_ALSA, name="Kore 2 Controller")
        self.midi_out = rtmidi.MidiOut(rtapi=rtmidi.API_LINUX_ALSA, name="Kore 2 Controller")
        self.input_byte_parser = mido.Parser()
        
    def connect(self):
        self.midi_in.set_callback(self.handle_midi_message_from_daw)
        self.midi_in.open_virtual_port("Kore 2 Controller MIDI 1")  
        print(self.midi_in.get_current_api())
        self.midi_out.open_virtual_port("Kore 2 Controller MIDI 1")
        print(self.midi_out.get_current_api())
        pass

    def handle_midi_bytes_from_controller(self, bytes):
        byte_list = list(bytes)

        if len(byte_list) < 3:
            return
        
        for byte in byte_list[2:]:
            self.input_byte_parser.feed_byte(byte)
        while self.input_byte_parser.pending() > 0:
            msg = self.input_byte_parser.get_message()
            if msg is not None:
                self.midi_out.send_message(msg.bytes())

    def handle_midi_message_from_daw(self, message):
        print("handle_midi_message:", message)
        # TODO: split and send MIDI data
        # Need to see if the controller can handle
        # Being sent a whole message at once, or if it
        # Only wants single bytes and just dumbly passes them
        # to the output

    def input_queue_consumer_func(self):
        parser = mido.Parser()
        current_message = None

        while True:
            if self.shutdown_event.is_set():
                return
            
            try:
                byte = self.input_byte_queue.get(timeout=1)
                parser.feed_byte(byte)
            except Exception as e:
                pass

            while parser.pending() > 0:
                current_message = parser.get_message()
                if current_message is not None:
                    self.midi_out.send_message(current_message.to_bytes())

    def disconnect(self):
        self.midi_out.close_port()
        self.midi_in.close_port()
        pass