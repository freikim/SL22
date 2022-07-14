import requests
import random
import cv2
import numpy as np

from kivy.app import App
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.graphics.texture import Texture
from kivy.properties import StringProperty, NumericProperty
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.image import Image
from kivy.uix.label import Label
from kivy.uix.screenmanager import ScreenManager, Screen

IMG_SIZE = 512

YELLOW_KEY = 'g'
BLUE_KEY = 'b'
WHITE_KEY = 'h'
BLACK_KEY = 's'


def load_stylegan_avatar():
    print('new avatar')
    url = "https://thispersondoesnotexist.com/image"
    r = requests.get(url, headers={'User-Agent': "My User Agent 1.0"}).content

    image = np.frombuffer(r, np.uint8)
    image = cv2.imdecode(image, cv2.IMREAD_COLOR)
    image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

    image = cv2.resize(image, (IMG_SIZE, IMG_SIZE))
    return image


class ButtonRow(BoxLayout):
    yellow_button = StringProperty(None)
    blue_button = StringProperty(None)
    white_button = StringProperty(None)
    black_button = StringProperty(None)

    def __init__(self, **kwargs):
        super(ButtonRow, self).__init__(**kwargs)
        self.size_hint_max_y = 150

    def on_yellow_button(self, instance, value):
        self.build_btn(value, 'images/large_yellow_arcade.png')

    def on_blue_button(self, instance, value):
        self.build_btn(value, 'images/large_blue_arcade.png')

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
        self.fake_person = []
        self._timer = None

    def setup_persons(self):
        print('on_build', self.ids)
        fake_row = self.ids['fake_row']
        for i in range(3):
            self.fake_person.append(Image())
            fake_row.add_widget(self.fake_person[-1])

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
    idx = NumericProperty(0)
    videos = [
        'videos/vocodes_video_JWINF2kb4vy9hqph994zbmq0e0khchm.mp4',
        'videos/vocodes_video_JWINFe8289c79rt5czjgp2w7t915tp1.mp4',
        'videos/vocodes_video_JWINFs0e28zvdpswjfdved778xxhasm.mp4'
    ]

    def on_keyboard(self, key):
        if key == WHITE_KEY:
            if self.idx == len(self.videos) - 1:
                self.idx = 0
            else:
                self.idx += 1
        elif key == BLACK_KEY:
            if self.idx == 0:
                self.idx = len(self.videos) - 1
            else:
                self.idx -= 1


class CameraAndPlaybackScreen(Screen):

    def __init__(self, **kwargs):
        super(CameraAndPlaybackScreen, self).__init__(**kwargs)
        self._timer = None
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
        self.ids['image1'].texture = texture1


class Screens(ScreenManager):

    def __init__(self, **kwargs):
        super(Screens, self).__init__(**kwargs)
        self._keyboard = Window.request_keyboard(self._keyboard_closed, self, 'text')
        print('Keyboard:', self._keyboard)
        self._keyboard.bind(on_key_down=self.on_keyboard_down)
        self._inactivity_timer = Clock.schedule_interval(self._inactive, 30)
        self._activity = False

    def _keyboard_closed(self):
        self._keyboard.unbind(on_key_down=self.on_keyboard_down)
        self._keyboard = None

    def on_keyboard_down(self, keyboard, keycode, text, modifiers):
        self._activity = True
        if keycode[1] == YELLOW_KEY:
            print('screens:', self.screens)
            print('go to screen: ', self.next())
            self.current = self.next()
        elif keycode[1] in [BLUE_KEY, BLACK_KEY, WHITE_KEY]:
            self.current_screen.on_keyboard(keycode[1])
        elif keycode[1] == 'escape':
            App.get_running_app().stop()

        return True

    def _inactive(self, dt):
        if not self._activity:
            if not self.current == 'intro':
                self.current = 'intro'
        self._activity = False


class SL22App(App):
    pass


if __name__ == '__main__':
    # Window.fullscreen = 'auto'
    SL22App().run()
