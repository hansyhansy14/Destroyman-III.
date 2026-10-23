import sys
from PyQt6 import QtWidgets, QtGui, QtCore
import random
import os
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


def app_dir():
    """Folder next to the exe (frozen) or next to this script."""
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))

POSITION_FILE = os.path.join(app_dir(), "position.txt")


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

drag_enabled = False   # "Drag Sprite" mode (window accepts mouse input)
dragging = False       # true only while the mouse button is held down
drag_offset = QtCore.QPoint(0, 0)
SQUISH_SHIFT = 10      # the bob moves the window down this many px when squished

# base_x / base_y = window top-left when NOT squished. This is what gets saved.
base_x = 0
base_y = 0

url = "https://raw.githubusercontent.com/hansyhansy14/destroyman-the-third/main/dist/resources/speeches.txt"
skin_index = 0
mirrored = False

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


def squish_offset():
    return SQUISH_SHIFT if is_squished else 0


def default_position():
    screen_geom = app.primaryScreen().geometry()
    x = screen_geom.x() + int(screen_geom.width() * anchor_x_ratio) - 200
    y = screen_geom.y() + int(screen_geom.height() * anchor_y_ratio) - 200
    return x, y


def load_position():
    """returns (x, y) from position.txt, or None if missing/invalid/off-screen."""
    try:
        with open(POSITION_FILE, "r", encoding="utf-8") as f:
            x_str, y_str = f.read().strip().split(",")
            x, y = int(x_str), int(y_str)
    except (OSError, ValueError):
        return None

    # make sure the sprite would actually be visible on some screen
    sprite_rect = QtCore.QRect(x, y, 200, 200)
    for screen in app.screens():
        if screen.availableGeometry().intersects(sprite_rect):
            return x, y
    return None


def save_position():
    try:
        with open(POSITION_FILE, "w", encoding="utf-8") as f:
            f.write(f"{base_x},{base_y}")
    except OSError as e:
        print("failed to save position: ", e)


class DraggableWindow(QtWidgets.QWidget):
    def mousePressEvent(self, event):
        global dragging, drag_offset
        if drag_enabled and event.button() == QtCore.Qt.MouseButton.LeftButton:
            dragging = True
            drag_offset = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()
        else:
            event.ignore()

    def mouseMoveEvent(self, event):
        global base_x, base_y
        if dragging:
            new_pos = event.globalPosition().toPoint() - drag_offset
            self.move(new_pos)
            base_x = new_pos.x()
            base_y = new_pos.y() - squish_offset()
            event.accept()
        else:
            event.ignore()

    def mouseReleaseEvent(self, event):
        global dragging
        if dragging and event.button() == QtCore.Qt.MouseButton.LeftButton:
            dragging = False
            save_position()
            event.accept()
        else:
            event.ignore()


def apply_window_flags():
    """make the window click-through (normal) or grabbable (drag mode)."""
    flags = (
        QtCore.Qt.WindowType.FramelessWindowHint |
        QtCore.Qt.WindowType.WindowStaysOnTopHint |
        QtCore.Qt.WindowType.Tool
    )
    if not drag_enabled:
        flags |= QtCore.Qt.WindowType.WindowTransparentForInput

    pos = window.pos()
    window.setWindowFlags(flags) # vvv resetting flags hides window so we need to show it again vvv
    window.move(pos)
    window.show()                # here
    window.raise_()


def toggle_drag_mode():
    global drag_enabled, dragging
    drag_enabled = not drag_enabled
    if not drag_enabled and dragging:
        dragging = False
        save_position()
    apply_window_flags()


def normalized_pixmap(path):
    pixmap = QtGui.QPixmap(path)
    pixmap = pixmap.scaled(
        sprite_size[0],
        sprite_size[1],
        QtCore.Qt.AspectRatioMode.IgnoreAspectRatio,
        QtCore.Qt.TransformationMode.SmoothTransformation
    )

    if mirrored:
        pixmap = pixmap.transformed(
            QtGui.QTransform().scale(-1, 1),
            QtCore.Qt.TransformationMode.SmoothTransformation
        )

    return pixmap

def mirror_sprite():
    global mirrored, sprite

    mirrored = not mirrored

    sprite = sprite.transformed(
        QtGui.QTransform().scale(-1, 1),
        QtCore.Qt.TransformationMode.SmoothTransformation
    )

    label.setPixmap(sprite)


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

    # don't yank the window out of the user's hand while dragging 'cause that kept happening hahu
    if not dragging:
        window.move(base_x, base_y + squish_offset())


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


class Bridge(QtCore.QObject):
    """pystray calls menu callbacks from its own thread; Qt widgets must only be
    touched from the main thread. emitting a signal queues the call onto it."""
    toggle_drag = QtCore.pyqtSignal()

bridge = Bridge()
bridge.toggle_drag.connect(toggle_drag_mode)


def quit_app(icon, item):
    icon.stop()
    QtCore.QTimer.singleShot(0, app.quit)


font_path = resource_path("resources/fonts/Fondamento-Regular.ttf")
font_id = QtGui.QFontDatabase.addApplicationFont(font_path)

if font_id == -1:
    fondamento_family = "Arial"
else:
    fondamento_family = QtGui.QFontDatabase.applicationFontFamilies(font_id)[0]


window = DraggableWindow()
window.setWindowFlags(
    QtCore.Qt.WindowType.FramelessWindowHint |
    QtCore.Qt.WindowType.WindowStaysOnTopHint |
    QtCore.Qt.WindowType.Tool |
    QtCore.Qt.WindowType.WindowTransparentForInput
)

window.setAttribute(QtCore.Qt.WidgetAttribute.WA_TranslucentBackground)
window.setFixedSize(200, 400)

# restore the saved position, or fall back to the default top-right anchor
saved = load_position()
base_x, base_y = saved if saved else default_position()

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
        MenuItem("Mirror Sprite", mirror_sprite),
        MenuItem(
            "Drag Sprite",
            lambda icon, item: bridge.toggle_drag.emit(),
            checked=lambda item: drag_enabled
        )
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