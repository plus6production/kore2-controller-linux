from PIL import Image, ImageDraw, ImageFont

class MixerView:
    def __init__(self, num_faders=8, bg_color=0, width=128, height=64, vu_max_val=1024, fader_max_val=1024):
        self.bg_color = bg_color
        self.width = width
        self.height = height
        self.vu_max = vu_max_val
        self.fader_max = fader_max_val
        self.fader_sprite = []
        self.modes = ['vol', 'pan', 'fx']
        self.num_faders = num_faders

        self.sprite_paths = {
            'fader' : './img/sprites/Mixer_Fader_13x56x4.png',
            'vol' : './img/sprites/Mixer_Vol_13x13x2.png',
            'pan' : './img/sprites/Mixer_Pan_13x13x2.png',
            'fx' : './img/sprites/Mixer_FX_13x13x2.png',
        }

        self.sprites = {
            'fader' : [],
            'vol' : [],
            'pan' : [],
            'fx' : []
        }

        self.split_sprite_to_array('fader', 4)
        self.split_sprite_to_array('vol', 2, False)
        self.split_sprite_to_array('pan', 2, False)
        self.split_sprite_to_array('fx', 2, False)

        self.canvas = Image.new('1', (self.width, self.height), color=1)
        self.font = ImageFont.truetype('./fonts/CG_pixel_3x5_mono.ttf', size=5)
        self.fader_top_offset = (self.canvas.size[1] - self.sprites['fader'][0].size[1])

        current_pos = [0, 0]
        for x in range(num_faders):
            # render fader outline           
            fader_pos = (current_pos[0], current_pos[1] + self.fader_top_offset)
            self.canvas.paste(self.sprites['fader'][0], fader_pos)
            current_pos[0] += 14
        
        # now the basic canvas is prepped. Frame rendering will use a copy of the canvas


    def split_sprite_to_array(self, name, num_frames, split_horiz=True):
        sprites = Image.open(self.sprite_paths[name], 'r').convert('1')
        w, h = sprites.size

        if split_horiz:
            frame_step = w / num_frames
            for x in range(num_frames):
                self.sprites[name].append(sprites.crop(((x*frame_step), 0, (x+1)*frame_step, h)))
        else:
            frame_step = h / num_frames
            for x in range(num_frames):
                self.sprites[name].append(sprites.crop((0, (x*frame_step), w, (x+1)*frame_step)))

    def render_frame(self, state):
        # TODO: Need to lock our data so that values don't change while we're
        # in the middle of this render, OR only retrieve the data here
        # How do we set it up so that the data is provided to or accessible by this class?
        # TODO: For efficiency, this (or the outer logic) could only perform a frame update
        # if the relevant controller state has changed (is dirty) since the last tick
        # Why does this all feel like I should be using a game engine?

        frame = self.canvas.copy()
        draw = ImageDraw.Draw(frame)

        # build initial scene
        current_pos = [0, 0]
        for x in range(len(state['track'])):
            # render name
            name = state['track'][x]['name'] if state['track'][x]['name'] != '' else '   '
            if len(name) > 3:
                name = name[:3]
            text_pos = (current_pos[0] + 1, current_pos[1] + 2)
            draw.text(text_pos, name, fill=0, font=self.font)

            # Draw fader vu:
            # TODO: calibrate 0dB line
            max_vert_pixels = 42
            vu_top_offset = 12
            horiz_pixels = 3
            horiz_off = 6
            vert_pixels = self.convert_range_to_pixels(state['track'][x]['vu'], (0, self.vu_max), (0, 42))
            #vert_pixels = int(max_vert_pixels * (state['track'][x]['vu'] / self.vu_max))
            if vert_pixels > 0:
                rectangle_top_bound_rel = max_vert_pixels + vu_top_offset - vert_pixels
                rectangle_bottom_bound_rel = 53
                rectangle_left_bound_rel = 5
                rectangle_right_bound_rel = 7
                rectangle_bounds = [
                    current_pos[0] + rectangle_left_bound_rel,
                    current_pos[1] + rectangle_top_bound_rel + self.fader_top_offset,
                    current_pos[0] + rectangle_right_bound_rel,
                    current_pos[1] + rectangle_bottom_bound_rel + self.fader_top_offset
                ]

                draw.rectangle(rectangle_bounds, fill=0)

            # Draw fader level
            max_vert_pixels = 43
            level_top_offset = 10
            level_left_offset_rel = 2
            level_line_len = 8
            vert_pixels = self.convert_range_to_pixels(state['track'][x]['volume'], (0, self.fader_max), (0, 43))
            line_y_pos = max_vert_pixels + level_top_offset - vert_pixels
            line_endpoints = [
                current_pos[0] + level_left_offset_rel,
                current_pos[1] + line_y_pos + self.fader_top_offset,
                current_pos[0] + level_left_offset_rel + level_line_len,
                current_pos[1] + line_y_pos + self.fader_top_offset,
            ]
            draw.line(line_endpoints, fill=0, width=1)

            current_pos[0] += 14
        
        # Render the mode inicators
        current_pos = [frame.size[0] - 14, 1]
        frame.paste(self.sprites['vol'][1], current_pos)

        return frame
    
    def convert_range_to_pixels(self, in_val, in_range, out_range):
        ratio = in_val / (in_range[1] - in_range[0])
        scaled_out = ((out_range[1] - out_range[0]) * ratio) + out_range[0]
        return int(scaled_out)
