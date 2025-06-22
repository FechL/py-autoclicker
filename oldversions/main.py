from pynput import mouse
from pynput.mouse import Button, Controller
from pynput.mouse import Listener
import threading
import time

mouse_controller = Controller()
clicking = False

def auto_right_click():
    while True:
        if clicking:
            mouse_controller.press(Button.right)
            mouse_controller.release(Button.right)
            time.sleep(0.07)  # kecepatan klik (semakin kecil semakin cepat)
        else:
            time.sleep(0.05)

def on_click(x, y, button, pressed):
    global clicking
    # Mouse 5 biasanya dianggap Button.button8
    if button == Button.button8:
        clicking = pressed

click_thread = threading.Thread(target=auto_right_click)
click_thread.daemon = True
click_thread.start()

with Listener(on_click=on_click) as listener:
    listener.join()
