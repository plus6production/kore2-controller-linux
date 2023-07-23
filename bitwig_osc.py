# This file handles an "event-based" (really queue-based) interface between
# a controller and the Bitwig OSC plugin created by Moss
# Incoming OSC messages are translated to an internal representation
# A consumer can "subscribe" to an OSC event and that event will begin to be
# added to the queue
# A producer can add formatted event to the incoming queue and they will be
# translated back to OSC and sent in the order that they are received
# In the future it might be handy to have multiple inbound and outbound queues,
# assuming I ever want to connect this up to multiple controllers at once
# (and I probably will)

import json
import queue
from pythonosc.udp_client import SimpleUDPClient
from pythonosc.osc_server import BlockingOSCUDPServer
from pythonosc.dispatcher import Dispatcher
import threading
from multiprocessing import pool
from osc_connection import OscConnection

# Will need to register callback functions for useful groups of functionality
# Eventually I would like operations to be context-sensitive as well
# Who is responsible for keeping track of and switching contexts based on
# received OSC messages?
# The controller is responsible for mapping its button presses to internal message representations
# and/or functions, and for "subscribing" to and handling inbound events
# We just need to translate OSC to a useful internal representation here and emit it to consumers

# Context schema?
# Mixer/track control
#   in:
#      track vus
#      track mutes
#      track solos
#      track volumes
#      track pans
#      track names
#      track selected
#      current bank
#      playing
#      recording
#   out:
#      track volumes
#      track pans
#      track mutes
#      track solos
#      track arm
#      track select
#      bank +/-
#      play
#      record
#      stop
# Arrangement view
# Clip view
# Browser

# Simplest proof of concept would be to get/set mute state for now and ignore everything else

class BitwigOsc:
    def __init__(self, event_callback, recv_address='127.0.0.1', recv_port=9000, send_address='127.0.0.1', send_port=8000):

        self.osc_connection = OscConnection(recv_address, recv_port, send_address, send_port)

        self.controller_to_osc_queue = queue.SimpleQueue()
        self.osc_to_controller_queue = queue.SimpleQueue()

        self.shutdown_event = threading.Event()
        self.is_connected = False

        self.osc_mapping_file = open('bitwig_osc.json', 'r')
        self.osc_mappings = json.load(self.osc_mapping_file)

        # Consumer will override this
        self.event_callback = event_callback

        # 2 threads:
        # 1. receive data from the OSC connection and pass it to consumer,
        # 2. convert data from the consumer and pass it to the OSC connection
        self.thread_pool = pool.ThreadPool(2)
    
    def connect(self):
        self.thread_pool.apply_async(self.controller_to_osc_worker)
        self.thread_pool.apply_async(self.osc_to_controller_worker)
        self.osc_connection.connect(self.queue_osc_message)
        self.is_connected = True

    # PARAMS:
    # message: { 'address' : OSC address, 'args' : list of arguments }
    def queue_osc_message(self, addr, *args):
        print("queue osc msg:", addr, list(args))
        # TODO: is it better to convert here and potentially block the
        # receiving OSC server, or convert on a separate thread and require
        # another buffer from internal to controller?
        self.osc_to_controller_queue.put({'address' : addr, 'args' : list(args) })

    def controller_to_osc_worker(self):        
        while True:
            if self.shutdown_event.is_set():
                # TODO: does this need to clean up anything?
                return
            
            data = None

            try:
                # Use a timeout so we can check our shutdown flag
                # every second.
                data = self.controller_to_osc_queue.get(timeout=1)
            except Exception as e:
                # TODO: Currently not concerned with timeouts,
                # though maybe we have a count of timeouts before we
                # become concerned.
                continue

            self.convert_and_send_controller_to_osc(data)

    def osc_to_controller_worker(self):
        while True:
            if self.shutdown_event.is_set():
                # TODO: does this need to clean up anything?
                return
            
            msg = None

            try:
                # Use a timeout so we can check our shutdown flag
                # every second.
                msg = self.osc_to_controller_queue.get(timeout=1)
            except Exception as e:
                # TODO: Currently not concerned with timeouts,
                # though maybe we have a count of timeouts before we
                # become concerned.
                print(e)
                continue

            self.convert_and_send_osc_to_controller(msg)

    def convert_and_send_osc_to_controller(self, data):
        print("convert and send:", data)
        # Convert received OSC data to internal representation
        # and send to the controller
        # FOR NOW, just split, check if there's a handler, and call the handler
        addr_list= data['address'].split('/')[1:]  # split leaves an empty string in index zero because of the leading slash
        print(addr_list)
        event = self.convert_message_to_event(addr_list, data['args'])
        self.event_callback(event)


    def convert_message_to_event(self, addr_list, args):
        event = {
            'context' : addr_list[0],
            'args' : args
        }
        
        if len(addr_list) == 1:
            return event

        if event['context'] == 'track':
            if addr_list[1].isnumeric():
                event['track'] = int(addr_list[1])
            elif addr_list[1] == 'selected':
                event['track'] = 'selected'
            else:
                event['track'] = 'global'
            
            if event['track'] !='global':
                if addr_list[2] != 'clip':
                    event['name'] = addr_list[2]
                else:
                    # SKIP FOR NOW?
                    return event
            else:
                # SKIP FOR NOW?
                return event
        
        print(event)
        return event

         

    def convert_and_send_controller_to_osc(self, data):
        pass


    def convert_and_queue_received_osc(self, addr, *args):
        # Convert received data to internal representation
        # and queue it for consumers
        pass

    def disconnect(self):
        self.shutdown_event.set()
        
        # TODO: do we need to somehow signal any consumer/producer classes
        # to stop producing?
        
