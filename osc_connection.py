# This class will generically

import queue
from pythonosc.udp_client import SimpleUDPClient
from pythonosc.osc_server import BlockingOSCUDPServer
from pythonosc.dispatcher import Dispatcher
import threading
from multiprocessing import pool
from pubsub import pub

class OscConnection:
    def __init__(self, recv_address='127.0.0.1', recv_port=9000, send_address='127.0.0.1', send_port=8000):
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

        self.shutdown_event = threading.Event()
        self.is_connected = False

        self.sub_to_daw = pub.subscribe(self.convert_and_send_received_sub, 'daw.to')

        # Either 2 or 3 threads, will see if another is needed
        self.thread_pool = pool.ThreadPool(2) # queue consumer / OSC sender, queue producer / OSC receiver

    def connect(self):
        self.dispatcher.set_default_handler(self.convert_and_publish_received_osc)
        self.thread_pool.apply_async(self.osc_sender_thread)
        self.thread_pool.apply_async(self.osc_receiver_thread)
        self.is_connected = True

    # Simple thread to read the input queue and send the message
    def osc_sender_thread(self):
        print('osc_sender_thread start')
        osc_client = SimpleUDPClient(self.send_address, self.send_port)
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
                #print("ERROR: osc_sender_thread:", e)
                continue

            print('OSC SEND', msg['address'], msg['args'])
            osc_client.send_message(msg['address'], msg['args'])
        print('osc_sender_thread end')

    def osc_receiver_thread(self):
        # We've given the server a thread to do its work,
        # so just let it do its thing.  To shut it down,
        # we can call its close() method from another thread.
        self.osc_server.serve_forever()

    def pubsub_daw_to_handler(self):
        while True:
            if self.shutdown_event.is_set():
                # TODO: does this need to clean up anything?
                return

    def handle_send_data(self, data):
        # Convert sent data to OSC
        pass

    def convert_and_publish_received_osc(self, addr, *args):
        print("convert and publish:", addr)
        # Convert received OSC data to pub/sub representation
        # and send to the controller
        topic = self.convert_osc_address_to_topic(addr, 'from')
        print(topic)
        pub.sendMessage(topic, arg1=topic, arg2=list(args))

    def convert_osc_address_to_topic(self, address, direction):
        addr_list= address.split('/')[1:]  # split leaves an empty string in index zero because of the leading slash      
        topic = 'daw' + '.' + direction
        for part in addr_list:
            topic += '.' + part

        return topic

    # Due to how pubsub appears to work, I need to duplicate data
    # by making arg1 also be the pubsub topic, and arg2 is actual args (in a list)
    def convert_and_send_received_sub(self, arg1, arg2):
        print('convert_and_send_received_sub')
        print(arg1)
        print(arg2)
        address = self.convert_topic_to_osc_address(arg1)
        print(address)
        self.send_message(address, arg2)

    def convert_topic_to_osc_address(self, topic):
        topic_list = topic.split('.')[2:] # remove the "daw.to"
        address = ''
        for part in topic_list:
            address += '/' + part
        
        return address

    # "Send" a message by placing in the queue to be sent
    # This allows a calling thread to not be directly involved in
    # any socket operations.
    def send_message(self, address, args_list):
        self.osc_send_queue.put({ 'address' : address, 'args' : args_list })

    def disconnect(self):
        self.shutdown_event.set()
        self.osc_server.server_close()
        
