import requests
import random
import glob
import cv2
import numpy as np

from kivy.app import App
from kivy.config import Config
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.graphics.texture import Texture
from kivy.properties import StringProperty, NumericProperty, BooleanProperty, DictProperty
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.image import Image
from kivy.uix.screenmanager import ScreenManager, Screen

from predictor_local import PredictorLocal
from utils import resize, crop

from texts import texts_da, texts_en

IMG_SIZE = 256

YELLOW_KEY = 'h'
BLUE_KEY = 's'
WHITE_KEY = 'b'
BLACK_KEY = 'g'


def load_images(IMG_SIZE=256):
    avatars = []
    filenames = []
    images_list = sorted(glob.glob(f'avatars/*'))
    for i, f in enumerate(images_list):
        if f.endswith('.jpg') or f.endswith('.jpeg') or f.endswith('.png'):
            img = cv2.imread(f)
            if img is None:
                print("Failed to open image: {}".format(f))
                continue

            if img.ndim == 2:
                img = np.tile(img[..., None], [1, 1, 3])
            img = img[..., :3][..., ::-1]
            img = resize(img, (IMG_SIZE, IMG_SIZE))
            avatars.append(img)
            filenames.append(f)
    return avatars, filenames


def load_stylegan_avatar():
    print('new avatar')
    url = "https://thispersondoesnotexist.com/image"
    try:
        r = requests.get(url, headers={'User-Agent': "My User Agent 1.0"})
    except:
        return None

    if not r.status_code == 200:
        return None

    image = np.frombuffer(r.content, np.uint8)
    image = cv2.imdecode(image, cv2.IMREAD_COLOR)
    image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

    image = cv2.resize(image, (IMG_SIZE, IMG_SIZE))
    return image


def draw_rect(img, rw=0.6, rh=0.8, color=(255, 0, 0), thickness=2):
    h, w = img.shape[:2]
    l = w * (1 - rw) // 2
    r = w - l
    u = h * (1 - rh) // 2
    d = h - u
    img = cv2.rectangle(img, (int(l), int(u)), (int(r), int(d)), color, thickness)


def draw_calib_text(frame, texts, thk=2, fontsz=0.5, color=(0, 0, 255)):
    frame = frame.copy()
    cv2.putText(frame, texts['placement'], (40, 20), 0, fontsz * IMG_SIZE / 255, color, thk)
    cv2.putText(frame, texts['calibrate'], (60, 245), 0, fontsz * IMG_SIZE / 255, color, thk)
    return frame


class ButtonRow(BoxLayout):
    yellow_button = StringProperty(None)
    blue_button = StringProperty(None)
    white_button = StringProperty(None)
    black_button = StringProperty(None)

    def __init__(self, **kwargs):
        super(ButtonRow, self).__init__(**kwargs)
        self.yel_btn = None
        self.blu_btn = None
        self.whi_btn = None
        self.blk_btn = None

    def on_yellow_button(self, instance, value):
        if not self.yel_btn:
            self.yel_btn = self.build_btn(value, 'images/large_white_arcade.png')
        else:
            self.yel_btn.ids['text'].text = value

    def on_blue_button(self, instance, value):
        if not self.blu_btn:
            self.blu_btn = self.build_btn(value, 'images/arcade_red.png')
        else:
            self.blu_btn.ids['text'].text = value

    def on_white_button(self, instance, value):
        if not self.whi_btn:
            self.whi_btn = self.build_btn(value, 'images/white_arcade.png')
        else:
            self.whi_btn.ids['text'].text = value

    def on_black_button(self, instance, value):
        if not self.blk_btn:
            self.blk_btn = self.build_btn(value, 'images/black_arcade.png')
        else:
            self.blk_btn.ids['text'].text = value

    def build_btn(self, btn_txt, file):
        cnt = ArcadeButton(text=btn_txt, file=file)
        self.add_widget(cnt)
        return cnt


class ArcadeButton(BoxLayout):
    text = StringProperty()
    file = StringProperty()


class IntroScreen(Screen):

    def restart_video(self):
        if 'intro_video' in self.ids:
            intro_video = self.ids['intro_video']
            intro_video.state = intro_video.state if not intro_video.state == 'stop' else 'play'

    def on_keyboard(self, key):
        intro_video = self.ids['intro_video']
        if key == YELLOW_KEY:
            self.manager.current = 'persons'
        if key == WHITE_KEY:
            App.get_running_app().lang = 'da'
            intro_video.state = 'stop'
            intro_video.position = 0
            intro_video.state = 'play'
        if key == BLACK_KEY:
            App.get_running_app().lang = 'en'
            intro_video.state = 'stop'
            intro_video.position = 0
            intro_video.state = 'play'


class FakePersonAnswerScreen(Screen):
    correct = BooleanProperty(False)

    def on_keyboard(self, key):
        if key == YELLOW_KEY:
            self.manager.current = 'camfun'


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
        if frame is not None:
            buf1 = cv2.flip(frame, 0)
            buf = buf1.tobytes()
            texture1 = Texture.create(size=(IMG_SIZE, IMG_SIZE))
            texture1.blit_buffer(buf, bufferfmt='ubyte')
            pos.texture = texture1

    def on_keyboard(self, key):
        manager = self.manager
        answer_screen = manager.get_screen('fake_answer')

        if key == WHITE_KEY:
            answer_screen.correct = True
            manager.current = 'fake_answer'
        elif key == BLACK_KEY or key == BLUE_KEY:
            answer_screen.correct = False
            manager.current = 'fake_answer'
        # elif key == YELLOW_KEY:
        #    manager.current = 'camfun'
        #    return


class VideoScreen(Screen):
    idx = NumericProperty(0)
    videos = [
        'videos/vocodes_video_JWINF2kb4vy9hqph994zbmq0e0khchm.mp4',
        'videos/vocodes_video_JWINFe8289c79rt5czjgp2w7t915tp1.mp4',
        'videos/vocodes_video_JWINF9rrr2tvhancam06b16v41dnat5.mp4'
    ]

    def on_enter(self):
        if 'player' in self.ids:
            intro_video = self.ids['player']
            intro_video.state = 'play'
            intro_video.options = {'eos': 'stop'}

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
        elif key == BLUE_KEY:
            intro_video = self.ids['player']
            intro_video.state = 'play'
        elif key == YELLOW_KEY:
            self.manager.current = 'outro1'


class CameraAndPlaybackScreen(Screen):

    def __init__(self, **kwargs):
        super(CameraAndPlaybackScreen, self).__init__(**kwargs)
        self._timer = None
        self.capture = cv2.VideoCapture(0)
        self.capture.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        self.capture.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        predictor_args = {
            'config_path': 'fomm/config/vox-adv-256.yaml',
            'checkpoint_path': 'vox-adv-cpk.pth.tar',
            'relative': True,
            'adapt_movement_scale': True,
            'enc_downscale': False
        }
        self.is_calibrated = False
        self.predictor = PredictorLocal(**predictor_args)
        self.cur_avatar = 0
        self.avatar = None
        self.avatar_kp = None
        self.kp_source = None
        self.avatars, self.avatar_names = load_images()

    def on_enter(self, *args):
        self._timer = Clock.schedule_interval(self.update, 1.0 / 33.0)
        self.cur_avatar = 0
        self.change_avatar(self.avatars[self.cur_avatar])
        self.is_calibrated = False
        print('Scheduled...')

    def on_leave(self, *args):
        Clock.unschedule(self._timer)
        self._timer = None

    def update(self, dt):
        frame_proportion = 0.9
        frame_offset_x = 0
        frame_offset_y = 0

        ret, frame = self.capture.read()
        frame = frame[..., ::-1]

        frame, (frame_offset_x, frame_offset_y) = crop(frame, p=frame_proportion, offset_x=frame_offset_x,
                                                       offset_y=frame_offset_y)
        frame = resize(frame, (IMG_SIZE, IMG_SIZE))[..., :3]

        preview_frame = frame.copy()
        draw_rect(preview_frame)
        if not self.is_calibrated:
            preview_frame = draw_calib_text(preview_frame, App.get_running_app().texts)
        self.ids['camera'].texture = self.to_texture(preview_frame)

        if self.is_calibrated:
            predicted = self.predictor.predict(frame)
            self.ids['avatar'].texture = self.to_texture(predicted)
        else:
            pic = self.avatars[self.cur_avatar]
            pic = resize(pic, (IMG_SIZE, IMG_SIZE))[..., :3]
            self.ids['avatar'].texture = self.to_texture(pic)

    def to_texture(self, frame):
        buf1 = cv2.flip(frame, 0)
        buf = buf1.tobytes()
        texture = Texture.create(size=(frame.shape[1], frame.shape[0]), colorfmt='rgb')
        texture.blit_buffer(buf, colorfmt='rgb', bufferfmt='ubyte')
        return texture

    def change_avatar(self, new_avatar):
        self.avatar_kp = self.predictor.get_frame_kp(new_avatar)
        self.kp_source = None
        self.avatar = new_avatar
        self.predictor.set_source_image(self.avatar)

    def on_keyboard(self, key):
        if key == WHITE_KEY:
            self.cur_avatar -= 1
            if self.cur_avatar < 0:
                self.cur_avatar = len(self.avatars) - 1
            self.change_avatar(self.avatars[self.cur_avatar])
        elif key == BLACK_KEY:
            self.cur_avatar += 1
            if self.cur_avatar >= len(self.avatars):
                self.cur_avatar = 0
            self.change_avatar(self.avatars[self.cur_avatar])
        elif key == BLUE_KEY:
            self.predictor.reset_frames()
            self.is_calibrated = True
        elif key == YELLOW_KEY:
            self.manager.current = 'videos'


class Outro1(Screen):

    def on_keyboard(self, key):
        if key == YELLOW_KEY:
            self.manager.current = 'intro'
        elif key == BLACK_KEY:
            self.manager.current = 'outro2'


class Outro2(Screen):

    def on_keyboard(self, key):
        if key == YELLOW_KEY:
            self.manager.current = 'intro'
        elif key == BLACK_KEY:
            self.manager.current = 'outro3'


class Outro3(Screen):

    def on_keyboard(self, key):
        if key == YELLOW_KEY:
            self.manager.current = 'intro'


class Screens(ScreenManager):

    def __init__(self, **kwargs):
        super(Screens, self).__init__(**kwargs)
        self._keyboard = Window.request_keyboard(self._keyboard_closed, self, 'text')
        # print('Keyboard:', self._keyboard)
        self._keyboard.bind(on_key_down=self.on_keyboard_down)
        self._inactivity_timer = Clock.schedule_interval(self._inactive, 45)
        self._debounce_timer = Clock.schedule_interval(self._debounce, 0.3333333333)
        self._last_key = None
        self._activity = False

    def _keyboard_closed(self):
        self._keyboard.unbind(on_key_down=self.on_keyboard_down)
        self._keyboard = None

    def on_keyboard_down(self, keyboard, keycode, text, modifiers):
        self._activity = True
        key = keycode[1]
        if key == 'shift':
            return True
        print('keypress: ', key, self._last_key)
        if key == self._last_key:
            return True
        self._last_key = key
        if key in [YELLOW_KEY, BLUE_KEY, BLACK_KEY, WHITE_KEY]:
            self.current_screen.on_keyboard(key)
        elif key == 'escape':
            App.get_running_app().stop()

        return True

    def _inactive(self, dt):
        if not self._activity:
            if not self.current == 'intro':
                self.current = 'intro'
        self._activity = False

    def _debounce(self, dt):
        self._last_key = None


class SL22App(App):
    texts = DictProperty(texts_da)
    lang = StringProperty('da')

    def on_lang(self, instance, value):
        if self.lang == 'da':
            self.texts = texts_da
        else:
            self.texts = texts_en


if __name__ == '__main__':
    Config.set('graphics', 'minimum_width', '1920')
    Config.set('graphics', 'minimum_height', '1080')
    Window.fullscreen = 'fake'
    Window.size = (1920, 1080)
    SL22App().run()
