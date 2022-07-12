import random
import requests

from kivy.app import App
from kivy.core.window import Window
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.gridlayout import GridLayout
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.videoplayer import VideoPlayer
from kivy.uix.image import Image
from kivy.clock import Clock
from kivy.graphics.texture import Texture
from kivy.properties import StringProperty

import cv2
import numpy as np

IMG_SIZE = 512


def load_stylegan_avatar():
    url = "https://thispersondoesnotexist.com/image"
    r = requests.get(url, headers={'User-Agent': "My User Agent 1.0"}).content

    image = np.frombuffer(r, np.uint8)
    image = cv2.imdecode(image, cv2.IMREAD_COLOR)
    image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

    image = cv2.resize(image, (IMG_SIZE, IMG_SIZE))
    return image


class ButtonRow(BoxLayout):

    red_button = StringProperty(None)
    green_button = StringProperty(None)
    white_button = StringProperty(None)
    black_button = StringProperty(None)

    def __init__(self, **kwargs):
        super(ButtonRow, self).__init__(**kwargs)
        self.size_hint_max_y = 200

    def on_red_button(self, instance, value):
        self.build_btn(value, 'images/large_red_arcade.png')

    def on_green_button(self, instance, value):
        self.build_btn(value, 'images/large_green_arcade.png')

    def on_white_button(self, instance, value):
        self.build_btn(value, 'images/white_arcade.png')

    def on_black_button(self, instance, value):
        self.build_btn(value, 'images/black_arcade.png')

    def build_btn(self, btn_txt, file):
        cnt = BoxLayout()
        btn = Image(source=file)
        cnt.add_widget(btn)
        lbl = Label()
        lbl.text = btn_txt
        cnt.add_widget(lbl)
        self.add_widget(cnt)


class IntroScreen(Screen):
    pass


class FakePersonAnswerScreen(Screen):
    pass


class NonExistingPeopleScreen(Screen):

    def __init__(self, **kwargs):
        super(NonExistingPeopleScreen, self).__init__(**kwargs)
        self._timer = None
        self.layout = BoxLayout(orientation='vertical')
        self.add_widget(self.layout)
        self.label = Label(text="Du vil nu få vist nogle forskellige mennesker.\nHvad er ligheden mellem dem?\nTryk på en af svarknapperne.")
        self.layout.add_widget(self.label)
        self.fake_row = BoxLayout()
        self.fake_person = []
        for i in range(3):
            self.fake_person.append(Image())
            self.fake_row.add_widget(self.fake_person[-1])
        self.layout.add_widget(self.fake_row)

    def on_enter(self, *args):
        self.new_person(None)
        self._timer = Clock.schedule_interval(self.new_person, 5)

    def on_leave(self, *args):
        Clock.unschedule(self._timer)
        self._timer = None

    def new_person(self, dt):
        pos = None
        for i in range(3):
            if not self.fake_person[i].texture:
                pos = self.fake_person[i]
                break
        if not pos:
            pos = random.choice(self.fake_person)
        frame = load_stylegan_avatar()
        buf1 = cv2.flip(frame, 0)
        buf = buf1.tobytes()
        texture1 = Texture.create(size=(IMG_SIZE, IMG_SIZE))
        texture1.blit_buffer(buf, bufferfmt='ubyte')
        pos.texture = texture1


class VideoScreen(Screen):

    def __init__(self, **kwargs):
        super(VideoScreen, self).__init__(**kwargs)
        self.layout = GridLayout()
        self.add_widget(self.layout)
        self.layout.cols = 1
        self.player = VideoPlayer(source='videos/vocodes_video_JWINF2kb4vy9hqph994zbmq0e0khchm.mp4')
        self.layout.add_widget(self.player)
        print('Videos screen initialized')

    def on_enter(self, *args):
        print('Videos screen entered')
        self.player.state = 'play'

    def on_leave(self, *args):
        self.player.state = 'stop'


class CameraAndPlaybackScreen(Screen):

    def __init__(self, **kwargs):
        super(CameraAndPlaybackScreen, self).__init__(**kwargs)
        self._timer = None
        self.layout = GridLayout()
        self.add_widget(self.layout)
        self.layout.cols = 2
        self.image1 = Image()
        self.image2 = Image()
        self.layout.add_widget(self.image1)
        self.layout.add_widget(self.image2)
        self.capture = cv2.VideoCapture(0)

    def on_enter(self, *args):
        self._timer = Clock.schedule_interval(self.update, 1.0 / 33.0)
        print('Scheduled...')

    def on_leave(self, *args):
        Clock.unschedule(self._timer)
        self._timer = None

    def update(self, dt):
        ret, frame = self.capture.read()
        buf1 = cv2.flip(frame, 0)
        buf = buf1.tobytes()
        texture1 = Texture.create(size=(frame.shape[1], frame.shape[0]), colorfmt='bgr')
        texture1.blit_buffer(buf, colorfmt='bgr', bufferfmt='ubyte')
        self.image1.texture = texture1


class Screens(BoxLayout):
    def __init__(self, **kwargs):
        super(Screens, self).__init__(**kwargs)
        self._keyboard = Window.request_keyboard(self._keyboard_closed, self, 'text')
        self._keyboard.bind(on_key_down=self.on_keyboard_down)

        self.sm = ScreenManager()
        self.sm.add_widget(IntroScreen(name='intro'))
        self.sm.add_widget(CameraAndPlaybackScreen(name='camfun'))
        self.sm.add_widget(VideoScreen(name='videos'))
        self.sm.add_widget(NonExistingPeopleScreen(name='persons'))
        self.sm.add_widget(FakePersonAnswerScreen(name='fake_answer'))
        self.sm.current = 'intro'
        self.add_widget(self.sm)

    def _keyboard_closed(self):
        self._keyboard.unbind(on_key_down=self.on_keyboard_down)
        self._keyboard = None

    def on_keyboard_down(self, keyboard, keycode, text, modifiers):
        if keycode[1] == 'n':
            self.sm.current = self.sm.next()
        elif keycode[1] == 'escape':
            App.get_running_app().stop()

        return True


class SL22App(App):

    def build(self):
        return Screens()


if __name__ == '__main__':
    # Window.fullscreen = 'auto'
    SL22App().run()
