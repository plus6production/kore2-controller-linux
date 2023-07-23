# This class will generically

import queue
from pythonosc.udp_client import SimpleUDPClient
from pythonosc.osc_server import BlockingOSCUDPServer
from pythonosc.dispatcher import Dispatcher
import threading
from multiprocessing import pool

class OscConnection:
    def __init__(self, recv_address='127.0.0.1', recv_port=9000, send_address='127.0.0.1', send_port=8000):
        # Set bogus callback that just returns the input data,
        # this should be configured by the consumer class
        self.receive_callback = lambda data : data

        # Set up OSC server, but don't start it
        self.recv_address = recv_address
        self.recv_port = recv_port
        self.dispatcher = Dispatcher()
        # Do not provide handlers to the dispatcher yet - the consuming class will do so
        self.osc_server = BlockingOSCUDPServer((self.recv_address, self.recv_port), self.dispatcher)

        # Set up OSC client, but don't start it
        self.send_address = send_address
        self.send_port = send_port

        self.osc_send_queue = queue.SimpleQueue()
        self.osc_receive_queue = queue.SimpleQueue()

        self.shutdown_event = threading.Event()
        self.is_connected = False

        # Either 2 or 3 threads, will see if another is needed
        self.thread_pool = pool.ThreadPool(2) # queue consumer / OSC sender, queue producer / OSC receiver

    def connect(self, receive_callback):
        self.receive_callback = receive_callback
        self.dispatcher.set_default_handler(receive_callback)
        self.thread_pool.apply_async(self.osc_sender_thread)
        self.thread_pool.apply_async(self.osc_receiver_thread)
        self.is_connected = True

    # Simple thread to read the input queue and send the message
    def osc_sender_thread(self):
        osc_client = udp_client.SimpleUDPClient(self.send_address, self.send_port)
        while True:
            if self.shutdown_event.is_set():
                # TODO: does this need to clean up anything?
                return
            
            msg = None

            try:
                # Use a timeout so we can check our shutdown flag
                # every second.
                msg = self.osc_send_queue.get(timeout=1)
            except Exception as e:
                # TODO: Currently not concerned with timeouts,
                # though maybe we have a count of timeouts before we
                # become concerned.
                continue

            osc_client.send_message(msg['address'], msg['args'])

    def osc_receiver_thread(self):
        # We've given the server a thread to do its work,
        # so just let it do its thing.  To shut it down,
        # we can call its close() method from another thread.
        self.osc_server.serve_forever()

    def handle_send_data(self, data):
        # Convert sent data to OSC
        pass

    def convert_and_queue_received_osc(self, addr, *args):
        # Convert received data to internal representation
        # and queue it for consumers
        pass

    # "Send" a message by placing in the queue to be sent
    # This allows a calling thread to not be directly involved in
    # any socket operations.
    def send_message(self, address, *args):
        self.osc_send_queue.put({ 'address' : address, 'args' : list(args) })

    def disconnect(self):
        self.shutdown_event.set()
        self.osc_server.close()
        # TODO: do we need to somehow signal any consumer/producer classes
        # to stop producing?
        
