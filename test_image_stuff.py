from views.mixer.mixer import MixerView

view = MixerView()
view.faders[3]['vu'] = 512

frame = view.render_frame()

frame.save('test.png')