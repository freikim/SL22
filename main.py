import requests
import random
import glob
import cv2
import numpy as np

from kivy.app import App
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.graphics.texture import Texture
from kivy.properties import StringProperty, NumericProperty, BooleanProperty
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.image import Image
from kivy.uix.label import Label
from kivy.uix.screenmanager import ScreenManager, Screen

from predictor_local import PredictorLocal
from utils import resize, crop

IMG_SIZE = 256

YELLOW_KEY = 'g'
BLUE_KEY = 'b'
WHITE_KEY = 'h'
BLACK_KEY = 's'

texts = {
    'intro': '''
Med kunstig intelligens er det muligt at ændre videoer og billeder, så det oprindelige indhold bliver erstattet af noget andet.
Det kalder man Deep Fake. Her kan du se nogle eksempler på Deep Fake videoer og selv lege med at styre en kendts ansigt.
Videoen nedenunder er 80 af de bedste Deep Fakes, der er lavet.
''',
    'videos': '''
På fakeyou.com kan du lave dine egne små videoer, hvor en kendt person siger eller synder det, som du har optaget i en lydfil.
Vi har lavet nogle stykker, som du kan se her.

Tryk på knapperne for at springe frem og tilbage mellem videoerne.
    ''',
    'persons': '''
Her ser du billeder af nogle personer. Hvad har de til fælles?
    ''',
    'persons_explanation': '''
Grafikkort producenten Nvidia arbejdede i 2018 med at lave en kunstig
intelligens, der kunne afsløre falske billeder af ansigter. Under det
arbejde fandt de ud af, at man faktisk også kan få den samme kunstige
intelligens til at fremstille ansigter af mennesker,
der slet ikke eksisterer.

Faktisk viser undersøgelser at i 90% af tilfældene kan et menneske ikke afgøre, at der er tale om et falsk ansigt.

Kunne du spotte nogle falske ansigter?
Billederne har måske små fejl, der gør at du kan se at det er et falsk ansigt.
Meget ofte er der problemer med ansigtets symmetri og det er noget vi mennesker
er ret følsomme overfor. Specielt kan briller og øreringe se mærkeligt ud eller
sidde mærkeligt. Andre fejl, der tit optræder er mærkelige baggrunde,
specielt hvis der er mere end et ansigt i billedet. 
''',
    'camfun': '''
Nogle forskere arbejdede med at lære kunstig intelligens at bevæge et billede ud fra videooptagelser af en anden situation.
Det er der kommet denne lille sjove applikation ud af. Du kan styre nogle forskellige personer, som du burde kende,
ved at se ind i kameraet, få dit ansigt til at fylde den blå firkant og så trykke på knappen “Kalibrer billedet”.
Prøv at bevæge dig og tal, blink med øjnene, drej hovedet fra side til side.
Prøv også at ændre afstanden mellem kameraet og dit hovede.
Kan du se begrænsningerne i den kunstige intelligens? Det er ikke altid at resultatet ser super godt ud.

Denne software kan installeres på din PC og bruges til at ændre en optagelse af dig til noget andet,
når du f.eks. deltager i et Zoom møde eller er i Teams sammen med dine klassekammerater.
Hvis du vil hente det selv, så skal u nok være lidt skrap til engelsk og til PC’ere, men du kan
finde vejledningen på https://github.com/alievk/avatarify-desktop under Installation.
Du skal have en Gamer PC for grafikkortet bruges til beregningerne, der altså kræver en hel del,, når det skal være live video.
    ''',
    'outro': '''
Nu har du set nogle eksempler på hvordan man kan lave falske videoer og endda styre en anden person live
og dermed lave en falsk optræden på Zoom eller Teams. Det vi har vist her er harmløst og er bare sjov,
men i forbindelse med krigen i Ukraine har Rusland lavet en Deepfake med Ukraines præsident Zelensky,
hvor han siger til de Ukrainske styrker at de skal overgive sig og nedlægge våbnene. Den video var faktisk
ikke særligt god, så der er nok ingen, der ville tro på det uden lige at undersøge sagen nærmere.
Men nogle af de videoer du så på introduktionssiden er lavet super professionelt og kan være svære at afsløre
som falske. Nogle af dem kan du kun se er falske, fordi du ved, hvem der er den rigtige skuespiller i filmen.

Hvad nu hvis du ikke selv har lyst til at blive brugt i en Deepfake video?
Hvis du husker fra ‘Styr en kendt’, så havde teknologien nogle begrænsninger og den er ikke særligt god,
hvis det ikke er et portrætbillede, hvor man kigger lige i kameraet, man har af den, der skal styres.
Det samme gælder for deepfake videoer. Det virker bedst, hvis der er mange portrætbilleder. Deepfake videoerne
skal faktisk bruge rigtigt mange billeder af dig, for at lave noget, der er så overbevisende som dem i introvideoen.
Så overvej derfor hvor mange billeder og videoer du lægger af dig selv (og dine venner!) på sociale medier.
Prøv også at lave dine profilbilleder, så man altid ser dig fra siden.

Men hvad nu hvis nogen bruger et billede af dig til at lave en deepfake? Måske i en situation, som du slet ikke
har lyst til at andre skal se dig i. Hvad kan du så gøre?
For det første kan det være strafbart, så involver dine forældre eller andre voksne du stoler, f.eks. din spejderleder,
på og få det anmeldt til politiet. Mange forsikringsselskaber har også hjælp og dækning, hvis din digitale identitet
bliver misbrugt, så der kan der også være hjælp at hente. Sig også tydeligt til dem, du kender, at det er en deepfake
og du ikke har noget med det at gøre. Deepfaken er sikkert heller ikke særligt god, da det kræver mange timers arbejde
at lave en professionel deepfake, så du kan sikkert nemt pege på fejl i videoen, der viser det er en deepfake.

Men hvad så, hvis du i virkeligheden er blevet filmet i en situation, du helst ikke ville filmes i?
Så kan du jo påstå at det er en deepfake, nogen har lavet af dig!
'''
}


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
    r = requests.get(url, headers={'User-Agent': "My User Agent 1.0"}).content

    image = np.frombuffer(r, np.uint8)
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


def draw_calib_text(frame, thk=2, fontsz=0.5, color=(0, 0, 255)):
    frame = frame.copy()
    cv2.putText(frame, "FIT FACE IN RECTANGLE", (40, 20), 0, fontsz * IMG_SIZE / 255, color, thk)
    cv2.putText(frame, "W - ZOOM IN", (60, 40), 0, fontsz * IMG_SIZE / 255, color, thk)
    cv2.putText(frame, "S - ZOOM OUT", (60, 60), 0, fontsz * IMG_SIZE / 255, color, thk)
    cv2.putText(frame, "THEN PRESS X", (60, 245), 0, fontsz * IMG_SIZE / 255, color, thk)
    return frame


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

    def on_keyboard(self, key):
        if key == YELLOW_KEY:
            self.manager.current = 'persons'


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
        buf1 = cv2.flip(frame, 0)
        buf = buf1.tobytes()
        texture1 = Texture.create(size=(IMG_SIZE, IMG_SIZE))
        texture1.blit_buffer(buf, bufferfmt='ubyte')
        pos.texture = texture1

    def on_keyboard(self, key):
        manager = self.manager
        answer_screen = manager.get_screen('fake_answer')
        if key == YELLOW_KEY:
            manager.current = 'camfun'
            return
        elif key == WHITE_KEY:
            answer_screen.correct = True
        else:
            answer_screen.correct = False
        manager.current = 'fake_answer'


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
        elif key == YELLOW_KEY:
            self.manager.current = 'outro'


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
            preview_frame = draw_calib_text(preview_frame)
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


class Outro(Screen):

    def on_keyboard(self, key):
        if key == YELLOW_KEY:
            self.manager.current = 'intro'


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
        key = keycode[1]
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


class SL22App(App):
    texts = texts


if __name__ == '__main__':
    # Window.fullscreen = 'auto'
    SL22App().run()
