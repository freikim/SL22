from kivy.app import App
from kivy.core.window import Window
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.gridlayout import GridLayout
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.videoplayer import VideoPlayer
from kivy.uix.image import Image
from kivy.clock import Clock
from kivy.graphics.texture import Texture

import requests

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


class NonExistingPeopleScreen(Screen):

    def __init__(self, **kwargs):
        super(NonExistingPeopleScreen, self).__init__(**kwargs)
        self.layout = BoxLayout()
        self.add_widget(self.layout)
        self.fake_person = Image()
        self.layout.add_widget(self.fake_person)

    def on_enter(self, *args):
        Clock.schedule_interval(self.new_person, 5)

    def on_leave(self, *args):
        pass

    def new_person(self, dt):
        frame = load_stylegan_avatar()
        buf1 = cv2.flip(frame, 0)
        buf = buf1.tobytes()
        texture1 = Texture.create(size=(IMG_SIZE, IMG_SIZE))
        texture1.blit_buffer(buf, bufferfmt='ubyte')
        self.fake_person.texture = texture1


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
        self._timer = Clock.schedule_interval(self.update, 1.0/33.0)
        print('Scheduled...')

    def on_leave(self, *args):
        Clock.unschedule(self._timer)

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
        self.sm.add_widget(CameraAndPlaybackScreen(name='camfun'))
        self.sm.add_widget(VideoScreen(name='videos'))
        self.sm.add_widget(NonExistingPeopleScreen(name='persons'))
        self.sm.current = 'videos'
        self.add_widget(self.sm)

    def _keyboard_closed(self):
        self._keyboard.unbind(on_key_down=self.on_keyboard_down)
        self._keyboard = None

    def on_keyboard_down(self, keyboard, keycode, text, modifiers):
        print('The key', keycode, 'have been pressed')
        # Keycode is composed of an integer + a string
        # If we hit escape, release the keyboard
        if keycode[1] == 'n':
            print('switch screen to ', self.sm.next())
            self.sm.current = self.sm.next()

        # Return True to accept the key. Otherwise, it will be used by
        # the system.
        return True


class MyApp(App):

    def build(self):
        return Screens()


if __name__ == '__main__':
    MyApp().run()
