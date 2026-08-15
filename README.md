# Kore 2 Controller Linux

This program takes control of the obsolete Kore 2 Controller from Native Instruments and allows full control over device functionality.

## Software-controllable hardware

Most Native Instruments hardware has at least partial control of its functionality managed by the Native Instruments services/daemons on Windows/Mac.  This means that usually, things like button presses, encoders, scrub wheel, LED state, and the display contents are not actually handled by the device's firmware, but are instead handled by software.  In the absense of Native Instruments' software, the controller has limited to no functionality.  But, if we can figure out how to properly talk to the device, this opens up some interesting possibilities.

## Existing Linux functionality

Older NI devices used a proprietary USB protocol that has a handful of "opcodes" that the device sends and/or receives.  The Linux "snd-usb-caiaq" driver handles most of these - it creates a MIDI in/out device for the physical ports on the Kore 2 Controller, but it routes encoder and button input to /dev/event type inputs, with no option to change this.  The driver also doesn't configure or allow writing to the display.

## Functionality enabled by this program

This program enables the following:
- Loading the latest device firmware into device memory during startup
- Mapping of all controller buttons via pubsub events
- Mapping of encoder inputs via pubsub events
- Mapping of LEDs via pubsub events
- Drawing custom UI to the monochrome LCD display (128x64 px)
- OSC (mapped via pubsub)
- Simple mixer view that interfaces with Bitwig Studio (track volume, track record arm, visualize track vu, read track names, navigate track banks)

## How to use (Linux only)

Blacklist the snd-usb-caiaq kernel module.  A more device-specific approach could be to create a udev rule for vendor 0x17cc device 0x4712, but I never needed to do that so I don't have an example.

Install python3-pip, python3-venv, libusb-1.0-0-dev, libcap-dev:

`sudo apt install python3-pip python3-venv libusb-1.0-0-dev libcap-dev`

Create a venv:

`python3 -m venv ./.venv`

Activate the venv:

`source ./.venv/bin/activate`

Use pip to install the required packages:

`pip3 install -r requirements.txt`

Run main.py:

`python3 main.py`

Plug in your Kore2 Controller.


## TODOs

This is very much a work in progress, and this TODO list is for me:
- Finish handling device inputs/outputs
    - MIDI in (opcode 6)
    - MIDI out (opcode 7)
    - Footswitch and Pedal inputs (opcode 3)
    - Scrub wheel (single byte in opcode 4)
- Embed the retrieved serial number into the firmware data sent to the controller during init (currently my serial number is in there)
- Retrieve OSC values and set offsets before sending any data to a DAW so that tracks don't suddenly change volume (or other settings)
- Clean signal handling - shutdown is only clean right now via the console input loop, CTRL+C usually works (but sometimes gets stuck and requires a sigkill)
- Efficiency - works fine for me so far, but Python isn't the best choice for this.  Stretch goal is to maybe do a Rust overhaul once this is fully prototyped out.
- More controller contexts/views
- Add documentation for the following:
    - Configuring Bitwig Studio to communicate with the script
    - Configuring custom mappings
    - Creating custom UIs
    - Discovery phase stuff:
        - Old NI USB protocol
        - EZ-USB info
        - LCD screen and controller info
        - Sine-cosine encoder algorithm