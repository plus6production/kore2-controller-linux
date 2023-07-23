import usb1
import threading
import signal
from PIL import Image, ImageEnhance, ImageDraw, ImageFont, GifImagePlugin
from pythonosc import udp_client
import numpy
import time
import json
import asyncio

from kore_2_controller.kore_2_controller import Kore2Controller

def main():
    controller = Kore2Controller()
    controller.initialize()

    converted_frames = []
    imageObject = Image.open('img/test_waveform.gif')
    for frame in range(0, imageObject.n_frames):
        imageObject.seek(frame)
        temp = imageObject.resize((128, 128))
        temp1 = temp.crop((0, 32, 128, 96))
        temp2 = temp1.convert('1')
        converted_frames.append(temp2)

    while True:
        for frame in converted_frames:
            controller.display.write_buffer_to_display(frame, False)
            time.sleep(0.1)

    # Generate image for screen using PIL

    # img1 = Image.new('1', (128, 64), 1)
    # draw1 = ImageDraw.Draw(img1)

    # font = ImageFont.truetype("/usr/share/fonts/liberation/LiberationMono-Bold.ttf", size=64)
    # draw1.text((64, 0), "+6", 0, font=font, align="center")
    
    # img2 = Image.new('1', (128, 64), 1)
    # draw2 = ImageDraw.Draw(img2)
    # draw2.text((68, 0), "+6", 0, font=font, align="center")
    # draw2.line((10,10) + (118, 54), fill=1)
    # img2.save('test.png')

    # #buffer_arr = numpy.asarray(img)
    # #print("Shape:", buffer_arr.shape)
    # while True:
    #     # Set LCD backlight on
    #     #controller.leds.set_single_led('LCD', 48)
    #     controller.display.write_buffer_to_display(img1, False)
    #     time.sleep(1)
    #     # Set LCD backlight on
    #     #controller.leds.set_single_led('LCD', 32)
    #     controller.display.write_buffer_to_display(img2, False)
    #     time.sleep(1)

    should_send = 1
    while should_send > 0:
        should_send = int(input("1 to wait more, 0 to exit: "))

    controller.shutdown()
    print("END OF LINE")
    return


if __name__ == "__main__":
    main()