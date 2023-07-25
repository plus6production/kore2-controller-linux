from pubsub import pub

class MixerModel:
    def __init__(self):
        self.modes = ['vol', 'pan', 'fx']
        self.state = {
            'tracks' : [{ 'name' : '', 'vu' : 0, 'volume': 0, 'mute': False } for x in range(8)],
            'mode' : self.modes[0]
        }
        self.input_to_daw_mapping = {}
        for x in range(len(self.state['tracks'])):
            in_topic_base = 'controller.input.button.'
            out_topic_base = 'daw.to.track.'

            # Configure mute mapping
            self.input_to_daw_mapping[in_topic_base + 'btn.' + str(x+1)] = (out_topic_base + str(x+1) + '.mute', [])

            # Configure touch mapping
            self.input_to_daw_mapping[in_topic_base + 'touch.' + str(x+1)] = (out_topic_base + str(x+1) + '.select', [])

        for key in self.input_to_daw_mapping:
            print(key, self.input_to_daw_mapping[key])

        self.listeners = set()

    def subscribe_to_topics(self):
        self.listeners.add(self.update_state_from_daw, 'daw.from.track')
        self.listeners.add(self.handle_button_event, 'controller.input.button')

    # Splits the provided topic string into its parts and
    # removes the specified number of leading parts
    def split_and_strip_topic_to_list(self, topic, num_prefixes):
        return topic.split('.')[num_prefixes:]

    def update_state_from_daw(self, full_topic, arg_list):
        addr_list = self.split_and_strip_topic_to_list(arg1, 3)
        if addr_list[0].isnumeric():
            track_index = int(addr_list[0])
            if addr_list[1] == 'mute':
                if len(arg_list) > 0:
                    # Explicit mute mode set
                    self.state['tracks'][track_index]['mute'] = (int(arg_list[0]) == 1)
                else:
                    # Mute toggle
                    self.state['tracks'][track_index]['mute'] = not self.state['tracks'][track_index]['mute']
            elif addr_list[1] in self.state['tracks']:
                self.state['tracks'][track_index][addr_list[1]] = int(arg_list[0])
    

        

