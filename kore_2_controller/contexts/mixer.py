from pubsub import pub
import json
from utils import utils
import threading
import time
from timeit import default_timer as timer
from kore_2_controller.views.mixer import MixerView
import prctl

class MixerContext:
    def __init__(self, render_callback, tick_rate=0.1):
        self.modes = ['vol', 'pan', 'fx']
        self.state_lock = threading.Lock()
        self.state = {
            'track' : [{ 'name' : '', 'vu' : 0, 'volume': 0, 'recarm': False } for x in range(8)],
            'mode' : self.modes[0]
        }
        self.state_dirty = False

        self.topic_base = 'controller.context.mixer'
        self.mappings_path = './kore_2_controller/contexts/mixer.json'
        self.listeners = set()

        self.view = MixerView()
        self.tick_rate = tick_rate
        self.shutdown_event = threading.Event()
        self.render_thread = threading.Thread(target=self.render_loop, name="Render")
        self.render_callback = render_callback

    def activate_context(self):
        # Open the mappings file and load the mappings
        self.mappings_file = open(self.mappings_path, 'r')
        self.mappings = json.load(self.mappings_file)
        self.subscribe_to_mixer_topic()
        self.register_context_mappings()

        # Force Bitwig to send out a data blast
        # to set our initial state
        pub.sendMessage('daw.to.refresh', arg1='daw.to.refresh', arg2=[])
        self.render_thread.start()

    def deactivate_context(self):
        self.shutdown_event.set()
        self.render_thread.join()
        print("MixerContext: Joined render thread")
        self.unregister_context_mappings()
        self.mappings_file.close()

    def register_context_mappings(self):
        for group in self.mappings['groups']:
            for mapping in group['mappings']:
                # PyPubSub has problems with certain characters that are in the Bitwig OSC def, so replace them
                cleaned = utils.replace_invalid_characters(mapping)
                self.listeners.add(pub.subscribe(self.dispatch_mapped_event, mapping))

    def unregister_context_mappings(self):
        # TODO: need to verify that these get garbage collected
        # and go away
        self.listeners.clear()

    # Starts listening for 'controller.context.mixer' events
    def subscribe_to_mixer_topic(self):
        self.listeners.add(pub.subscribe(self.handle_mixer_event, self.topic_base))

    # Acquires the state lock and updates the state based on the provided
    # path and value
    def set_track_state(self, path_list, val, is_toggle):
        self.state_lock.acquire()
        if is_toggle:
            self.state[path_list[0]][int(path_list[1]) - 1][path_list[2]] = not self.state[path_list[0]][int(path_list[1])][path_list[2]]
        else:
            self.state[path_list[0]][int(path_list[1]) - 1][path_list[2]] = val
        
        # Indicate that the state has changed since the last "tick"
        self.state_dirty = True
        self.state_lock.release()

    def handle_mixer_event(self, arg1, arg2):
        addr_list = utils.split_and_strip_topic_to_list(arg1, 3)
        if addr_list[0] != 'track' or len(addr_list) != 3 or not addr_list[1].isnumeric():
            return
        
        is_toggle = False
        if len(arg2) == 0:
            # Command is toggling a value
            is_toggle = True

        self.set_track_state(addr_list, arg2[0], is_toggle)
    
    # Routes incoming events to their destination(s) based on the mapping file
    def dispatch_mapped_event(self, arg1, arg2):
        #print("Mixer dispatch:", arg1)
        for group in self.mappings['groups']:
            if arg1 in group['mappings']:
                for dest in group['mappings'][arg1]['dest']:
                    #print("Dispatch send:", dest, arg2)
                    cleaned = utils.replace_invalid_characters(dest)
                    pub.sendMessage(cleaned, arg1=cleaned, arg2=arg2)

    def render_loop(self):
        prctl.set_name("mix_render")
        frames_rendered = 0
        while True:
            if self.shutdown_event.is_set():
                return
            
            # Sleep till the next tick (approx)
            time.sleep(self.tick_rate)

            self.state_lock.acquire()

            # If there hasn't been a state update since the last tick,
            # don't render
            if not self.state_dirty:
                self.state_lock.release()
                continue

            # State has been updated, take a snapshot
            # so we can release the lock
            state = self.state.copy()

            # Indicate that the state is now "clean"
            self.state_dirty = False
            self.state_lock.release()

            # Get the frame from our view
            #start_time = timer()
            frame = self.view.render_frame(state)
            #end_time = timer()
            #frames_rendered += 0
            #print('frame', frames_rendered, 'took', (end_time - start_time) * 1000, 'ms')

            # Send the frame to the receiver
            self.render_callback(frame)


