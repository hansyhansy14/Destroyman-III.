import sys
from PyQt6 import QtWidgets, QtGui, QtCore
import random
import os
import sys
from pystray import Icon, Menu, MenuItem
from PIL import Image
import requests
import time
from pypresence import Client
import threading

rpc = Client(client_id="1491710882495987824")
def rpckeepalive():
    rpc.start()
    # keep alive
    while True:
        time.sleep(15)

def rpcsend(randomtext):
    rpc.send_data(1, {
        "cmd": "SET_ACTIVITY",
        "args": {
            "pid": 10000,
            "activity": {
                "details": f"{randomtext}",
                "assets": {
                    "large_image": "diii_evil", 
                    "large_text": "I am a huge annoyance!"
                }
            }
        },
        "nonce": "1"
    })

def resource_path(relative_path):
    if getattr(sys, 'frozen', False):
        base_path = sys._MEIPASS
        return os.path.join(base_path, relative_path)
    else:
        return os.path.join("dist", relative_path)


def get_speeches(url):
    try:
        response = requests.get(url, timeout=5)
        response.raise_for_status()
        lines = [line.strip() for line in response.text.splitlines() if line.strip()]
        return lines
    except Exception as e:
        print("failed to fetch speeches.txt: ", e)
        return None


sprite_size = (200, 200)
window = None
label = None
sprite = None
is_squished = False

url = "https://raw.githubusercontent.com/hansyhansy14/destroyman-the-third/main/dist/resources/speeches.txt"
skin_index = 0

skins = [
    "resources/skins/diii_normal.png",
    "resources/skins/diii_evil.png",
    "resources/skins/diii_whatsapp.png",
    "resources/skins/diii_discord.png",
    "resources/skins/diii_golf.png",
    "resources/skins/diii_linux.png",
    "resources/skins/diii_monster.png",
    "resources/skins/diii_cisco.png"
]

anchor_x_ratio = 1.0
anchor_y_ratio = 0.13


def normalized_pixmap(path):
    pixmap = QtGui.QPixmap(path)
    return pixmap.scaled(
        sprite_size[0],
        sprite_size[1],
        QtCore.Qt.AspectRatioMode.IgnoreAspectRatio,
        QtCore.Qt.TransformationMode.SmoothTransformation
    )


def cycle_back(icon=None, item=None):
    global skin_index, sprite
    skin_index = (skin_index - 1) % len(skins)
    sprite = normalized_pixmap(resource_path(skins[skin_index]))
    bob_squish()


def cycle_forth(icon=None, item=None):
    global skin_index, sprite
    skin_index = (skin_index + 1) % len(skins)
    sprite = normalized_pixmap(resource_path(skins[skin_index]))
    bob_squish()


def bob_squish():
    global is_squished, sprite, window, label

    is_squished = not is_squished

    width = 200
    height = 200 if not is_squished else 190

    screen = app.primaryScreen()
    screen_geom = screen.geometry()

    anchor_x = int(screen_geom.width() * anchor_x_ratio) - window.width()
    anchor_y = int(screen_geom.height() * anchor_y_ratio)

    window.move(anchor_x, anchor_y - height)


    if arms_timer is None:
        squished_pixmap = sprite.scaled(
            width, height,
            QtCore.Qt.AspectRatioMode.IgnoreAspectRatio,
            QtCore.Qt.TransformationMode.SmoothTransformation
        )
        label.setPixmap(squished_pixmap)


arms_timer = None

def start_arms_dc():
    global arms_timer
    arms_frame = [0]  # use list to mutate inside nested func

    def toggle():
        path = "resources/skins/diii_discord_happy_up.png" if arms_frame[0] % 2 == 0 \
               else "resources/skins/diii_discord_happy_down.png"
        label.setPixmap(normalized_pixmap(resource_path(path)))
        arms_frame[0] += 1

    arms_timer = QtCore.QTimer()
    arms_timer.timeout.connect(toggle)
    arms_timer.start(1000)

def stop_arms_dc():
    global arms_timer
    if arms_timer is not None:
        arms_timer.stop()
        arms_timer = None

def load_speeches(path):
    with open(path, 'r', encoding="utf-8") as f:
        return [line.strip() for line in f if line.strip()]


speeches = get_speeches(url)
if not speeches:
    speeches = load_speeches(resource_path("resources/speeches.txt"))

first_message_shown = False

def spawn_text():
    global first_message_shown, sprite
    text_label = QtWidgets.QLabel(window)

    restore_sprite = None
    '''turns discord skin into a happy lil noodle when he talks cause i love him most'''
    if skin_index == 0:
        restore_sprite = sprite
        sprite = normalized_pixmap(
            resource_path("resources/skins/diii_normal_happy.png")
        )
        label.setPixmap(sprite)
    if skin_index == 1:
        restore_sprite = sprite
        sprite = normalized_pixmap(
            resource_path("resources/skins/diii_evil_trulyevil.png")
        )
        label.setPixmap(sprite)

    if skin_index == 3:
        start_arms_dc()
    
    if skin_index == 5:
        restore_sprite = sprite
        sprite = normalized_pixmap(
            resource_path("resources/skins/diii_linux_typing.png")
        )
        label.setPixmap(sprite)
    

    if not first_message_shown:
        text_label.setText(
            "Thank you for contracting [ CORAL FEVER ]! I'm your new personal assistant, "
            "Destroyman III. I'll be your right hand - your emotional support buddy."
        )
        first_message_shown = True
    elif speeches:
        randomtext = random.choice(speeches)
        text_label.setText(randomtext)
        rpcsend(randomtext)
    else:
        text_label.setText("...")

    text_label.setStyleSheet(
        "background-color: lightgrey;"
        "border: 2px solid black;"
        "padding: 5px;"
        "color: black;"
    )

    text_label.setWordWrap(True)
    text_label.setMaximumWidth(window.width() - 20)

    font_size = 14
    text_label.setFont(QtGui.QFont(fondamento_family, font_size))
    text_label.adjustSize()

    delta = 70
    available_space = window.height() - label.height() - delta

    '''keeps making text smaller until it fits into the box'''
    while text_label.height() > available_space and font_size > 6:
        font_size -= 1
        text_label.setFont(QtGui.QFont(fondamento_family, font_size))
        text_label.adjustSize() # makes box bigger or smaller

    x = (window.width() - text_label.width()) // 2
    y = window.height() - label.height() + delta - text_label.height()

    text_label.move(x, y)
    text_label.show()

    def resetsmile():
        global sprite
        stop_arms_dc()
        text_label.deleteLater()
        if restore_sprite is not None:
            sprite = restore_sprite
            label.setPixmap(sprite)

    QtCore.QTimer.singleShot(10000, resetsmile)

    delay = random.randint(20000, 30000)
    QtCore.QTimer.singleShot(delay, spawn_text)


app = QtWidgets.QApplication(sys.argv)


def quit_app(icon, item):
    icon.stop()
    QtCore.QTimer.singleShot(0, app.quit)


font_path = resource_path("resources/fonts/Fondamento-Regular.ttf")
font_id = QtGui.QFontDatabase.addApplicationFont(font_path)

if font_id == -1:
    fondamento_family = "Arial"
else:
    fondamento_family = QtGui.QFontDatabase.applicationFontFamilies(font_id)[0]


window = QtWidgets.QWidget()
window.setWindowFlags(
    QtCore.Qt.WindowType.FramelessWindowHint |
    QtCore.Qt.WindowType.WindowStaysOnTopHint |
    QtCore.Qt.WindowType.Tool |
    QtCore.Qt.WindowType.WindowTransparentForInput
)

window.setAttribute(QtCore.Qt.WidgetAttribute.WA_TranslucentBackground)
window.setFixedSize(200, 400)

sprite = normalized_pixmap(resource_path(skins[skin_index]))

label = QtWidgets.QLabel(window)
label.setPixmap(sprite)
label.setFixedSize(200, 200)
label.show()

bob_squish()

window.show()
window.raise_()
window.activateWindow()


def create_tray_icon():
    image = Image.open(resource_path("resources/destroy.ico"))

    menu = Menu(
        MenuItem("Quit", quit_app),
        MenuItem("Change Skin (Cycle Forward)", cycle_forth),
        MenuItem("Change Skin (Cycle Back)", cycle_back),
    )

    icon = Icon("destroyman", image, "Destroyman III", menu)
    icon.run_detached()
    return icon


tray_icon = create_tray_icon()

bob_timer = QtCore.QTimer()
bob_timer.timeout.connect(bob_squish)
bob_timer.start(1000)

thread = threading.Thread(target=rpckeepalive, daemon=True)
thread.start()

QtCore.QTimer.singleShot(5000, spawn_text)

sys.exit(app.exec())