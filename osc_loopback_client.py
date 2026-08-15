from pythonosc.osc_server import ThreadingOSCUDPServer
from pythonosc.dispatcher import Dispatcher
from pythonosc.udp_client import SimpleUDPClient
from multiprocessing import pool

class OscLoopbackClient:
    def __init__(self, recv_port=8000, send_port=9000):
        self.dispatcher = Dispatcher()
        self.dispatcher.set_default_handler(self.handle_loopback)
        self.osc_server = ThreadingOSCUDPServer(('127.0.0.1', recv_port), self.dispatcher)
        self.osc_client = SimpleUDPClient('127.0.0.1', send_port)
        self.thread_pool = pool.ThreadPool(2)
        self.thread_pool.apply_async(self.osc_recv_thread)

    def __del__(self):
        self.osc_server.shutdown()

    def handle_loopback(self, address, *args):
        if address.find('volume') < 0:
            print(f"Received loopback message: {address} {args}")
        self.osc_client.send_message(address, args)

    def osc_recv_thread(self):
        self.osc_server.serve_forever()