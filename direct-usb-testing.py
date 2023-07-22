import usb1
import threading
import signal
from PIL import Image, ImageEnhance, ImageDraw, ImageFont
from pythonosc import udp_client
import numpy
import time
import json

from kore_2_controller.kore_2_controller import Kore2Controller

def main():
    controller = Kore2Controller()
    controller.initialize()

    # Generate image for screen using PIL

    img1 = Image.new('1', (128, 64), 1)
    draw1 = ImageDraw.Draw(img1)

    font = ImageFont.truetype("/usr/share/fonts/liberation/LiberationMono-Bold.ttf", size=64)
    draw1.text((64, 0), "+6", 0, font=font, align="center")
    
    img2 = Image.new('1', (128, 64), 1)
    draw2 = ImageDraw.Draw(img2)
    draw2.text((68, 0), "+6", 0, font=font, align="center")
    draw2.line((10,10) + (118, 54), fill=1)
    img2.save('test.png')

    #buffer_arr = numpy.asarray(img)
    #print("Shape:", buffer_arr.shape)
    while True:
        # Set LCD backlight on
        controller.leds.set_single_led(30, 48)
        controller.display.write_buffer_to_display(img1, False)
        time.sleep(1)
        # Set LCD backlight on
        controller.leds.set_single_led(30, 32)
        controller.display.write_buffer_to_display(img2, False)
        time.sleep(1)

    should_send = 1
    while should_send > 0:
        should_send = int(input("1 to wait more, 0 to exit: "))

    controller.shutdown()
    print("END OF LINE")
    return


if __name__ == "__main__":
    main()