# This is the file that handles all the underlying USB communications
# The Kore2 controller is based on an EZ-USB chip from Cypress, and as such
# responds to firmware download/upload commands.
# NI implemented a custom protocol over USB BULK transfers in/out, with a
# small set of opcodes and some fine-grained device control
import usb1
import threading
from multiprocessing import pool
import time
import sys
import json
from utils import utils
import queue
import prctl

firmware_packet_sequence = None

'''
#define EP1_CMD_GET_DEVICE_INFO	0x1
#define EP1_CMD_READ_ERP	0x2
#define EP1_CMD_READ_ANALOG	0x3
#define EP1_CMD_READ_IO		0x4
#define EP1_CMD_WRITE_IO	0x5
#define EP1_CMD_MIDI_READ	0x6
#define EP1_CMD_MIDI_WRITE	0x7
#define EP1_CMD_AUDIO_PARAMS	0x9
#define EP1_CMD_AUTO_MSG	0xb
#define EP1_CMD_DIMM_LEDS       0xc
'''

CMD_GET_DEVICE_INFO = 0x01
CMD_READ_ERP = 0x02
CMD_READ_ANALOG = 0x03
CMD_READ_IO = 0x04
CMD_WRITE_IO = 0x05
CMD_MIDI_READ = 0x06
CMD_MIDI_WRITE = 0x07
CMD_LCD_WRITE = 0x08
CMD_AUDIO_PARAMS = 0x09 # Unused on Kore2
CMD_AUTO_MSG = 0x0b
CMD_DIMM_LEDS = 0x0c

LCD_SUBCODE_SETUP = 0x0
LCD_SUBCODE_DATA = 0x1

endpoints = {
    'control_out' : 0x0,
    'control_in' : 0x80,
    'bulk_out' : 0x1,
    'bulk_in' : 0x81
}

class Kore2USB:
    def __init__(self, debug=False):
        self.vid = 0x17cc
        self.pid = 0x4712
        self.serial_number = ""
        self.debug = debug
        self.recv_queue = queue.SimpleQueue()
        self.send_queue = queue.SimpleQueue()
        self.thread_pool = pool.ThreadPool(4)
        self.endpoints = {
            'control_out' : 0x0,
            'control_in' : 0x80,
            'bulk_out' : 0x1,
            'bulk_in' : 0x81
        }
        self.opcode_map = {
            1 : self.handle_device_spec,
            2 : self.default_handler,
            3 : self.default_handler,
            4 : self.default_handler,
            6 : self.default_handler,
            8 : self.handle_display_opcode
        }

    def default_handler(self, data):
        utils.print_if_debug(self.debug, "Unhandled message:", list(data))

    # Access the controller via USB and begin handling
    # messages
    def open(self):
        self.usb_context = usb1.USBContext()
        self.usb_handle = None
        self.wait_for_device_handle()
        
        # Disconnect kernel driver from interface
        if self.usb_handle.kernelDriverActive(0):
            utils.print_if_debug(self.debug, "Kore2USB: Detaching existing kernel driver")
            self.usb_handle.detachKernelDriver(0)
        
        # Claim interface
        self.usb_handle.claimInterface(0)

        # Event to tell the polling thread to stop
        self.shutdown_event = threading.Event()
        self.handshake_complete_event = threading.Event()

        # Events specific to opcode 1 and 8, which
        # are expected to receive responses on the recv thread
        self.spec_received_event = threading.Event()
        self.op_8_received_event = threading.Event()

        # The USB polling thread is launched, but waits on the "handshake_complete_event"
        # to know when the full device startup sequence has been completed
        self.thread_pool.apply_async(self.poll_usb_thread_func)

        # Two receive queue handlers to allow parallel dispatch in cases when a lot of processing needs to be done
        # TODO: would be better to allow individual receive tasks to be applied on the fly
        # TODO: a process-global thread pool might be a better option overall, to reduce surprise thread creation
        self.thread_pool.apply_async(self.recv_queue_consumer_func)
        self.thread_pool.apply_async(self.recv_queue_consumer_func)

        # Single send handler
        self.thread_pool.apply_async(self.send_queue_consumer_func)

    def close(self):
        utils.print_if_debug(self.debug, "Kore2USB.close(): enter")
        self.shutdown_event.set()
        utils.print_if_debug(self.debug, "Kore2USB.close(): shutdown sent")
        self.thread_pool.close()
        self.thread_pool.join()
        print("Kore2Usb: Joined thread pool")
        if self.usb_handle:
            self.usb_handle.releaseInterface(0)
            self.usb_handle.close()
        if self.usb_context:
            self.usb_context.close()
        utils.print_if_debug(self.debug, "Kore2USB.close(): exit")
    
    # Function to spinwait with short sleep to detect the connected Kore2 controller
    # Note: this function doesn't handle multiple Kore2 controllers connected to the machine
    def wait_for_device_handle(self):
        while self.usb_handle is None:
            time.sleep(0.1)
            self.usb_handle = self.usb_context.openByVendorIDAndProductID(0x17cc, 0x4712)
    
    def queue_bulk_send(self, data):
        self.send_queue.put(data)

    def send_queue_consumer_func(self):
        prctl.set_name("usb_send_q")
        # We can let the send thread begin immediately
        while True:
            if self.shutdown_event.is_set():
                return
            
            data = None

            try:
                data = self.send_queue.get(timeout=1)
            except Exception as e:
                continue
            
            try:
                self.try_write_usb_bulk(endpoints['bulk_out'], data, 200)
            except Exception as e:
                print("USB send worker:", e, data)


    def recv_queue_consumer_func(self):
        prctl.set_name("usb_recv_q")
        # The setup logic handles receives directly until the handshake is complete
        self.handshake_complete_event.wait()

        while True:
            if self.shutdown_event.is_set():
                return
            
            data = None

            try:
                data = self.recv_queue.get(timeout=1)
            except Exception as e:
                continue
            
            try:
                self.handle_usb_message(data)
            except Exception as e:
                print("USB recv worker:", e, data)


    # The receive thread - this handles pulling USB BULK IN data from the controller
    # as it arrives
    def poll_usb_thread_func(self):
        prctl.set_name("usb_poll_bulk")
        placeholder_read_size = 256
        placeholder_timeout = 500
        # Don't clog up with reads until the handshake sequence is done
        self.handshake_complete_event.wait()

        while True:
            try:
                if self.shutdown_event.is_set():
                    return
                data = self.usb_handle.bulkRead(self.endpoints['bulk_in'], placeholder_read_size, placeholder_timeout)
                self.recv_queue.put(data)
            except Exception as e:
                utils.print_if_debug(self.debug, "Polling problem:", e)
    
    def send_firmware_sequence(self):
        with open('kore_2_controller/firmware_packets.json', 'r') as fd:
            firmware_packet_sequence = json.load(fd)

            # CPU RESET
            try:
                packet_repr = firmware_packet_sequence[0]
                utils.print_if_debug(self.debug, "Sending CPU reset")
                utils.print_if_debug(self.debug, packet_repr['request_type'], packet_repr['request'], packet_repr['value'], 0, packet_repr['data'])
                self.usb_handle.controlWrite(packet_repr['request_type'], packet_repr['request'], packet_repr['value'], 0, bytearray(packet_repr['data']))
            except Exception as e:
                utils.print_if_debug(self.debug, "ERROR first time setting CPU reset:", e)
                return

            for packet_repr in firmware_packet_sequence[1:-2]:
                #utils.print_if_debug(self.debug, packet_repr['request_type'], packet_repr['request'], packet_repr['value'], 0, packet_repr['data'])
                self.usb_handle.controlWrite(packet_repr['request_type'], packet_repr['request'], packet_repr['value'], 0, bytearray(packet_repr['data']))

            try:
                packet_repr = firmware_packet_sequence[-2]
                utils.print_if_debug(self.debug, "Sending CPU reset AGAIN")
                utils.print_if_debug(self.debug, packet_repr['request_type'], packet_repr['request'], packet_repr['value'], 0, packet_repr['data'])
                self.usb_handle.controlWrite(packet_repr['request_type'], packet_repr['request'], packet_repr['value'], 0, bytearray(packet_repr['data']))
            except Exception as e:
                utils.print_if_debug(self.debug, "ERROR second time setting CPU reset:", e)
                return

            try:
                packet_repr = firmware_packet_sequence[-1]
                utils.print_if_debug(self.debug, "Sending CPU RELEASE")
                utils.print_if_debug(self.debug, packet_repr['request_type'], packet_repr['request'], packet_repr['value'], 0, packet_repr['data'])
                self.usb_handle.controlWrite(packet_repr['request_type'], packet_repr['request'], packet_repr['value'], 0, bytearray(packet_repr['data']))
            except Exception as e:
                utils.print_if_debug(self.debug, "ERROR releasing CPU:", e)

            # Last step before sleep is to set the configuration to 0
            try:
                self.usb_handle.setConfiguration(0)
            except Exception as e:
                utils.print_if_debug(self.debug, 'ERROR setting config after firmware:', e)
            
            # Device will now reset, which means it disappears.  Need to somehow recapture the device
            self.usb_handle.releaseInterface(0)
            self.usb_handle.close()
            self.usb_handle = None
            time.sleep(1)
            self.wait_for_device_handle()

            # Disconnect kernel driver from interface
            if self.usb_handle.kernelDriverActive(0):
                utils.print_if_debug(self.debug, "Kore2USB: Detaching existing kernel driver")
                self.usb_handle.detachKernelDriver(0)
        
            # Claim interface
            self.usb_handle.claimInterface(0)

            current_config = self.usb_handle.getConfiguration()
            print("current_config", current_config)

            usb_mode = self.usb_handle.getASCIIStringDescriptor(3)
            print('mode:', usb_mode)

            try:
                self.usb_handle.setConfiguration(1)
            except Exception as e:
                utils.print_if_debug(self.debug, 'ERROR setting config after device reboot:', e)
            self.usb_handle.setInterfaceAltSetting(0, 1)

            usb_mode = self.usb_handle.getASCIIStringDescriptor(3)
            print('mode:', usb_mode)



    # The initial set of USB CONTROL and BULK messages to fully bring up the Kore 2 controller
    # with updated firmware and all the functionality that NI locks behind its software
    def start_handshake(self):
        # Need to do the get descriptor sequence
        
        current_config = self.usb_handle.getConfiguration()
        utils.print_if_debug(self.debug, "Current configuration:", current_config)
        
        # Send GET STATUS request, expected to return PIPE error
        try:
            status_data = self.usb_handle.controlRead(0x80, 0x0, 0, 0, 2, 100)
        except usb1.USBErrorPipe:
            utils.print_if_debug(self.debug, "Got expected pipe error on first status read")

        self.serial_number = self.usb_handle.getStringDescriptor(0x05, 0)
        
        try:
            self.usb_handle.setConfiguration(1)
        except usb1.USBErrorBusy:
            utils.print_if_debug(self.debug, "ERROR setting configuration to 1, busy")
        
        self.usb_handle.setInterfaceAltSetting(0, 1)

        # Send GET STATUS request, expected to return PIPE error
        try:
            status_data = self.usb_handle.controlRead(0x80, 0x0, 0, 0, 2, 100)
        except usb1.USBErrorPipe:
            utils.print_if_debug(self.debug, "Got expected pipe error on second status read")

        # Do zero-length bulk read?
        # self.usb_handle.bulkRead(0x81, 0, 100)

        # Initial device info read
        fw_ver = self.send_get_device_info(True)

        if fw_ver != 10:
            # Send the firmware data
            self.send_firmware_sequence()

            # Initial device info read
            fw_ver = self.send_get_device_info(True)
            assert fw_ver == 10


    def finalize_handshake(self):
        # Magic Linux driver packet
        # TODO: determine if this is limiting anything (like the number of available footswitch/pedal inputs)
        # Bytes are:
        # 0x1 - number of digital inputs (footswitches?)
        # 0xa - number of analog inputs
        # 0x5 - number of erp inputs (buttons/touch/scrub)
        data = bytearray([1, 10, 5])
        self.send_auto_msg_command(data, 200, True)
        self.handshake_complete_event.set()
        

    # Do a bulk read with timeout
    def try_read_usb_bulk(self, endpoint, length, timeout):
        try:
            return self.usb_handle.bulkRead(endpoints['bulk_in'], length, timeout)
        except Exception as e:
            print('ERROR during bulk recv:', e)
            return bytearray()

    # Do a bulk write with timeout
    def try_write_usb_bulk(self, endpoint, data, timeout):
        bytes_sent = 0

        try:
            bytes_sent = self.usb_handle.bulkWrite(endpoint, data, timeout)
        except Exception as e:
            print("ERROR sending command: ", e)

        #print("Sent", bytes_sent, "bytes to controller")
        return bytes_sent

    def send_bulk_command_buffer(self, command_buf, timeout, do_recv, recv_len=1):
        resp = None
        self.queue_bulk_send(command_buf)
        # Wait for reply
        if (do_recv):
            resp = self.try_read_usb_bulk(endpoints['bulk_in'], recv_len, timeout)       
        return resp

    # Send opcode 1 and receive the response, which is a list of
    # information about firmware version, number of ins/outs, etc
    # Currently just returns the received firmware version
    # TODO: handle the other data in this message
    def send_get_device_info(self, do_recv):
        # Send id request
        data = bytearray(1)
        data[0] = 0x01

        resp = self.send_bulk_command_buffer(data, 500, do_recv, 16)
        if resp is not None:
            info_list = list(resp)
            return info_list[1]
        
        # TODO: better handling of not getting firmware version
        return 0

    # Send opcode 8 (LCD commands) with the provided data
    # and wait for the expected single-byte response [8] from the controller
    def send_lcd_setup_command(self, data, timeout, do_recv):
        buf = bytearray(3)
        buf[0] = CMD_LCD_WRITE
        buf[1] = LCD_SUBCODE_SETUP # LCD subcode for data write to display memory
        buf[2] = len(data)
        buf.extend(data)

        resp = self.send_bulk_command_buffer(buf, timeout, do_recv, 1)
        return resp
    
    # Send data to be displayed on the LCD, provided as bytearray
    def send_lcd_data_command(self, data, timeout, do_recv):
        buf = bytearray(3)
        buf[0] = CMD_LCD_WRITE
        buf[1] = LCD_SUBCODE_DATA # LCD subcode for data write to display memory
        buf[2] = len(data)
        buf.extend(data)

        resp = self.send_bulk_command_buffer(buf, timeout, do_recv, 1)
        return resp
    
    def send_auto_msg_command(self, data, timeout, do_recv):
        buf = bytearray(1)
        buf[0] = CMD_AUTO_MSG
        buf.extend(data)

        resp = self.send_bulk_command_buffer(buf, timeout, do_recv, 1)
        return resp

    def send_led_command(self, data, timeout, do_recv=False):
        buf = bytearray(1)
        buf[0] = CMD_DIMM_LEDS
        buf.extend(data)

        if not self.handshake_complete_event.is_set():
            do_recv = True

        resp = self.send_bulk_command_buffer(buf, timeout, do_recv, 1)
        return resp
    
    def handle_usb_message(self, data):
        opcode = data[0]
        if opcode in self.opcode_map:
            self.opcode_map[opcode](data[1:])
        else:
            utils.print_to_file(list(data))

    def set_button_opcode_callback(self, handler_func):
        self.opcode_map[4] = handler_func

    def set_encoder_opcode_callback(self, handler_func):
        self.opcode_map[2] = handler_func

    # Handle opcode 0x1 from controller
    def handle_device_spec(self, data):
        self.spec_received_event.set()
        utils.print_to_file(list(data))

    def handle_display_opcode(self, data):
        self.op_8_received_event.set()
        #print_to_file("op 8")
