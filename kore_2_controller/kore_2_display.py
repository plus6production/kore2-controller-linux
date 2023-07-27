# This class handles the display-specific logic and sequencing for the Kore 2 controller
import time
import numpy
from PIL import Image, ImageEnhance, ImageDraw, ImageFont
from utils import utils
import threading
from queue import SimpleQueue
import prctl
from timeit import default_timer as timer

class Kore2Display:
    def __init__(self, usb_handler, debug=False):
        self.usb_handler = usb_handler
        self.debug = debug
        self.column_offset = 0x05
        self.display_size = {'width' : 128, 'height' : 64}
        self.brightness = 50 # 0-63
        self.frame_queue = SimpleQueue()
        self.previous_frame_parts = None
        self.shutdown_event = threading.Event()
        self.frame_consumer_thread = threading.Thread(target=self.frame_consumer_function, name="FrameCons")
    
    # Send the set of commands to initialize the LCD display
    def initialize(self):

        '''
        First display packet sent by NI:
        0x8:0x0:0xf:0xe2:0xa2:0xa1:0x81:0x0:0x2c:0x2e:0x2f:0x27:0x88:0xcc:0xef:0xb0:0x0:0x10
        e2 RESET
        a2 bias set 1/9
        a1 ADC set reverse
        81 00 ELEC VOL MODE SET 0
        2c Power control set 4
        2e Power control set 6
        2f Power control set 7
        27 VREG Ratio set 7
        88 **UNKNOWN
        cc **COM set reverse? (C8 + additional)
        ef **UNKNOWN, might be read/mod/write column increment
        b0 Page addr set 0
        00 ** Unknown
        10 Column addr set upper bit
        '''
        lcd_setup_commands = bytearray(12)
        lcd_setup_commands[0] = 0xe2 # RESET LCD
        lcd_setup_commands[1] = 0xa2 # Set bias levels 1/9
        lcd_setup_commands[2] = 0xa1 # ADC set reverse
        lcd_setup_commands[3] = 0x81 # Elec vol mode set CMD 
        lcd_setup_commands[4] = 0x00 # Elec vol mode register val 0
        lcd_setup_commands[5] = 0x2c # Power control set 1100
        lcd_setup_commands[6] = 0x2e # Power control set 1110
        lcd_setup_commands[7] = 0x2f # Power contol set 1111
        lcd_setup_commands[8] = 0x27 # VREGs
        lcd_setup_commands[9] = 0x88 # ?
        lcd_setup_commands[10] = 0xcc # Com set revers?
        lcd_setup_commands[11] = 0xef # R/M/W increment

        utils.print_if_debug(self.debug, "Sending initial LCD configuration to controller:", list(lcd_setup_commands))
        resp = self.usb_handler.send_lcd_setup_command(lcd_setup_commands, 200, True)
        utils.print_if_debug(self.debug, list(resp))

        time.sleep(0.2)

        # Write Startup image to screen before poweron
        self.write_png_to_display('img/Kore_Test_Scr_8bitgreyscale.png', True)

        '''
        Second group of setup commands sent by NI:
        0x8:0x0:0x1:0xe2        RESET
        0x8:0x0:0x1:0xa1        ADC SET REVERSE
        0x8:0x0:0x1:0xc8        COM SET REVERSE (c8 + 0)
        0x8:0x0:0x1:0xa2        LCD BIAS SET 1/9
        0x8:0x0:0x1:0x2c        POWER CONTROL SET 4
        0x8:0x0:0x1:0x2e        POWER CONTROL SET 6
        0x8:0x0:0x1:0x2f        POWER CONTROL SET 7
        0x8:0x0:0x1:0x27        VREG RATIO SET 7
        0x8:0x0:0x2:0x81:0x1    ELECTR VOL MODE SET 1
        0x8:0x0:0x1:0xa6        LCD DISPLAY SET NORMAL
        0x8:0x0:0x1:0x88        ***UNKNOWN***
        0x8:0x0:0x1:0xef        ***UNKNOWN*** - could be read/mod/write column increment 
        0x8:0x0:0x1:0xaf        DISPLAY ON
        '''
        lcd_setup_commands = bytearray(14)
        lcd_setup_commands[0] = 0xe2 # RESET LCD
        lcd_setup_commands[1] = 0xa1 # ADC set reverse
        lcd_setup_commands[2] = 0xc8 # Com set reverse
        lcd_setup_commands[3] = 0xa2 # Set bias levels 1/9
        lcd_setup_commands[4] = 0x2c # Power control set 1100
        lcd_setup_commands[5] = 0x2e # Power control set 1110
        lcd_setup_commands[6] = 0x2f # Power contol set 1111
        lcd_setup_commands[7] = 0x27 # VREGs
        lcd_setup_commands[8] = 0x81 # Elec vol mode set CMD 
        lcd_setup_commands[9] = 0x01 # Elec vol mode register val 0
        lcd_setup_commands[10] = 0xa6 # LCD display set normal direction
        lcd_setup_commands[11] = 0x88 # ?
        lcd_setup_commands[12] = 0xef # R/M/W increment
        lcd_setup_commands[13] = 0xaf # Display ON


        utils.print_if_debug(self.debug, "Sending second LCD configuration to controller:", list(lcd_setup_commands))
        resp = self.usb_handler.send_lcd_setup_command(lcd_setup_commands, 200, True)
        utils.print_if_debug(self.debug, list(resp))

        self.frame_consumer_thread.start()
    
    def frame_consumer_function(self):
        prctl.set_name("disp_frame_q")
        while True:
            if self.shutdown_event.is_set():
                return
            
            frame = None
            try:
                frame = self.frame_queue.get(timeout=0.5)
            except Exception as e:
                continue
            
            if frame is not None:
                #start_time = timer()
                self.write_buffer_to_display(frame)
                #end_time = timer()
                #print('write_buffer_to_display took', (end_time - start_time) * 1000, 'ms')

    def enqueue_frame(self, frame):
        self.frame_queue.put(frame)

    def write_buffer_to_display(self, buffer, manual_wait=False):
        # Set up unchanging values in command buffers for the three commands per transaction
        setup_cmd_buf = bytearray(3)
        lcd_page_base = 0xb0 # Final page num will be computed and set programmatically
        setup_cmd_buf[1] = self.column_offset # Column address low 4 bits - shifts the output horizontally to align it
        lcd_column_high4bits_base = 0x10  # Column address high 4 bits, will be computed

        buffer_arr = numpy.asarray(buffer).reshape(self.display_size['height'], self.display_size['width'])
        #print("Shape:", buffer_arr.shape)

        # Split the image into 32px x 8 px chunks
        chunks = []
        dirty_chunks = 0
        for page in range(8):
            chunks.append([])
            for line in range(4):
                # Get the submatrix at the necessary index
                start_col = line * 32
                start_row = page * 8
                chunk_data = buffer_arr[start_row:start_row+8,start_col:start_col+32]
                dirty = True
                if self.previous_frame_parts is not None:
                    dirty = not numpy.array_equal(chunk_data, self.previous_frame_parts[page][line])
                chunks[page].append(chunk_data)
                if dirty:
                    dirty_chunks += 1
                    setup_cmd_buf[0] = lcd_page_base + page # computed page address
                    setup_cmd_buf[2] = lcd_column_high4bits_base + (line * 2) # computed line address
                    flattened = chunk_data.T.flatten()
                    bit_flags_array = numpy.packbits(flattened, bitorder="little")
                    data_cmd_buf= bytearray(bit_flags_array.tobytes())
                    self.usb_handler.send_lcd_setup_command(setup_cmd_buf, 100, manual_wait)
                    self.usb_handler.send_lcd_data_command(data_cmd_buf, 200, manual_wait)
        #print("dirty_chunks:", dirty_chunks)
        self.previous_frame_parts = chunks

        # for page in range(8):
        #     for line in range(4):
        #         computed_page_addr = lcd_page_base + page
        #         computed_line_addr = lcd_column_high4bits_base + (line * 2)
        #         #print("Cmd1_B3:", computed_page_addr, "Cmd2_b4:", computed_line_addr)

        #         # Finalize the buffers
        #         setup_cmd_buf[0] = computed_page_addr
        #         setup_cmd_buf[2] = computed_line_addr

        #         # Get the submatrix at the necessary index
        #         start_col = line * 32
        #         start_row = page * 8

        #         assert start_row + 8 <= 64
        #         assert start_col + 32 <= 128

        #         # y value is a * 8
        #         submatrix = buffer_arr[start_row:start_row+8,start_col:start_col+32]
        #         flattened = submatrix.T.flatten()
        #         #flattened = numpy.fliplr(submatrix.T).flatten()
        #         #flattened = submatrix.flatten()
        #         bit_flags_array = numpy.packbits(flattened, bitorder="little")
        #         data_cmd_buf= bytearray(bit_flags_array.tobytes())

        #         #if b == 3:
        #         #    print(bit_flags_array)

        #         assert len(data_cmd_buf) == 32

        #         self.usb_handler.send_lcd_setup_command(setup_cmd_buf, 100, manual_wait)
        #         self.usb_handler.send_lcd_data_command(data_cmd_buf, 200, manual_wait)
        
    def write_png_to_display(self, path, manual_wait):
        img = Image.open(path)

        img_scaled = img.resize((128, 64))

        img_1b = img_scaled.convert('1')
        # img_1b.save('img/test.png')

        self.write_buffer_to_display(img_1b, manual_wait)

    def set_view_source(self, source):
        self.frame_source = source

    def shutdown(self):
        self.shutdown_event.set()
        self.frame_consumer_thread.join()
        print("Kore2Display: joined frame_consumer_thread")
        
