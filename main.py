import signal
import threading
from kore_2_controller.kore_2_controller import Kore2Controller
from osc_connection import OscConnection
import prctl

from osc_loopback_client import OscLoopbackClient

shutdown_event = threading.Event()

def signal_handler(sig, frame):
    print("Signal received, shutting down...")
    shutdown_event.set()


def main():
    prctl.set_name("main")

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    # This will start publishing osc messages as pubsub topics
    osc_connection = OscConnection()
    osc_connection.connect()

    # osc_loopback_client = OscLoopbackClient()

    controller = Kore2Controller()
    controller.initialize()

    print("Kore2 Controller is running. Press Ctrl+C to exit.")

    shutdown_event.wait()

    osc_connection.disconnect()
    controller.shutdown()
    print("END OF LINE")
    return


if __name__ == "__main__":
    main()