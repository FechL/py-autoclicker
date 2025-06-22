import tkinter as tk
from tkinter import ttk
from pynput.mouse import Button, Controller as MouseController, Listener as MouseListener
from pynput.keyboard import Listener as KeyboardListener, Key, KeyCode
import threading
import time
import json
import os
import webbrowser

mouse = MouseController()
clicking = False
toggle_state = False
config_file = 'pyautoclicker_config.json'
test_cps_count = 0
test_start_time = 0
waiting_for_trigger = False
current_listeners = []
last_click_time = 0
CLICK_IGNORE_THRESHOLD = 0.1

config = {
    'click_button': 'left',
    'trigger_key': 'x',
    'click_mode': 'hold',
    'cps': 10,
    'burst_count': 5,
    'burst_delay_ms': 100
}

def save_config():
    with open(config_file, 'w') as f:
        json.dump(config, f)

def load_config():
    global config
    if os.path.exists(config_file):
        with open(config_file, 'r') as f:
            config = json.load(f)

def get_button():
    return Button.left if config['click_button'] == 'left' else Button.right

def click_loop():
    global clicking, last_click_time
    while True:
        if clicking:
            if config['click_mode'] == 'burst':
                for _ in range(config['burst_count']):
                    last_click_time = time.time()
                    mouse.press(get_button())
                    mouse.release(get_button())
                    time.sleep(config['burst_delay_ms'] / 1000.0)
                clicking = False
            else:
                last_click_time = time.time()
                mouse.press(get_button())
                mouse.release(get_button())
                time.sleep(1 / config['cps'])
        else:
            time.sleep(0.05)


def stop_all_listeners():
    global current_listeners
    for listener in current_listeners:
        try:
            listener.stop()
        except:
            pass
    current_listeners = []

def on_keyboard_press(key):
    global clicking, waiting_for_trigger, toggle_state
    if waiting_for_trigger:
        try:
            if hasattr(key, 'char') and key.char is not None:
                config['trigger_key'] = key.char
            elif isinstance(key, Key):
                config['trigger_key'] = str(key).replace("Key.", "")
        except:
            config['trigger_key'] = str(key)
        update_trigger_label()
        waiting_for_trigger = False
        save_config()
        restart_listeners()
        return False

    try:
        if get_trigger_match(key):
            if config['click_mode'] == 'hold':
                clicking = True
            elif config['click_mode'] == 'toggle':
                toggle_state = not toggle_state
                clicking = toggle_state
            elif config['click_mode'] == 'burst':
                clicking = True
    except AttributeError:
        pass

def on_keyboard_release(key):
    global clicking
    try:
        if get_trigger_match(key) and config['click_mode'] == 'hold':
            clicking = False
    except AttributeError:
        pass

def on_mouse_click(x, y, button, pressed):
    global clicking, waiting_for_trigger, toggle_state, last_click_time

    if config['click_mode'] == 'burst':
        if time.time() - last_click_time < CLICK_IGNORE_THRESHOLD:
            return

    if waiting_for_trigger:
        config['trigger_key'] = str(button).replace("Button.", "")
        update_trigger_label()
        waiting_for_trigger = False
        save_config()
        restart_listeners()
        return False

    if str(button).replace("Button.", "") == config["trigger_key"]:
        if config['click_mode'] == 'hold':
            clicking = pressed
        elif config['click_mode'] == 'toggle' and pressed:
            toggle_state = not toggle_state
            clicking = toggle_state
        elif config['click_mode'] == 'burst' and pressed:
            clicking = True

def get_trigger_match(key):
    if isinstance(key, KeyCode):
        return key.char == config['trigger_key']
    elif isinstance(key, Key):
        return config['trigger_key'] == str(key).replace("Key.", "")
    return False

def start_listeners():
    global current_listeners
    stop_all_listeners()

    k_listener = KeyboardListener(on_press=on_keyboard_press, on_release=on_keyboard_release)
    m_listener = MouseListener(on_click=on_mouse_click)

    k_listener.start()
    m_listener.start()

    current_listeners = [k_listener, m_listener]

def restart_listeners():
    start_listeners()

def start_clicker_thread():
    t = threading.Thread(target=click_loop)
    t.daemon = True
    t.start()

def start_test_cps():
    global test_cps_count, test_start_time
    if test_cps_count == 0:
        test_start_time = time.time()
    test_cps_count += 1

def on_test_click(event):
    clicked_button = 'left' if event.num == 1 else 'right' if event.num == 3 else 'middle'
    if clicked_button == config['click_button']:
        start_test_cps()
        elapsed_time = time.time() - test_start_time
        if elapsed_time > 0:
            current_cps = test_cps_count / elapsed_time
            event.widget.config(text=f"Clicks: {test_cps_count} | CPS: {current_cps:.2f}")
        else:
            event.widget.config(text=f"Clicks: {test_cps_count}")

def reset_test_cps():
    global test_cps_count, test_start_time
    test_cps_count = 0
    test_start_time = 0

# UI
trigger_display_widget = None
cps_label = None
burst_count_var = None
burst_delay_var = None
cps_var = None
cps_label_widget = None
cps_spin = None
burst_count_spin = None
burst_delay_spin = None
delay_label = None

def update_trigger_label():
    if trigger_display_widget:
        trigger_display_widget.config(text=config['trigger_key'].upper())

def update_cps_label_text():
    return f"{config['click_button'].capitalize()} click here to test CPS"

def auto_save_and_restart():
    save_config()
    restart_listeners()

def update_cps_burst_fields():
    mode = config['click_mode']
    
    # Clear all widgets first
    for widget in cps_burst_frame.winfo_children():
        widget.grid_forget()

    if mode == 'burst':
        cps_label_widget.config(text="Burst click:")
        
        # Configure grid for burst mode: count | delay label | delay value
        cps_burst_frame.columnconfigure(0, weight=1, minsize=60)
        cps_burst_frame.columnconfigure(1, weight=0, minsize=80)
        cps_burst_frame.columnconfigure(2, weight=1, minsize=60)
        
        burst_count_spin.grid(row=0, column=0, sticky='ew')
        delay_label.grid(row=0, column=1, padx=(10, 5), sticky='w')
        burst_delay_spin.grid(row=0, column=2, sticky='ew')
    else:
        cps_label_widget.config(text="CPS (Clicks/s):")
        
        # Configure grid for CPS mode: full width for CPS spinbox
        cps_burst_frame.columnconfigure(0, weight=1, minsize=200)
        cps_burst_frame.columnconfigure(1, weight=0, minsize=0)
        cps_burst_frame.columnconfigure(2, weight=0, minsize=0)
        
        cps_spin.grid(row=0, column=0, columnspan=3, sticky='ew')

def validate_non_negative(var, default=1):
    try:
        if var.get() < 1:
            var.set(default)
    except:
        var.set(default)

def build_ui():
    global trigger_display_widget, cps_label, burst_count_var, burst_delay_var, cps_var
    global cps_label_widget, cps_spin, burst_count_spin, burst_delay_spin, cps_burst_frame, delay_label

    load_config()
    start_clicker_thread()
    start_listeners()

    root = tk.Tk()
    root.title("py-autoclicker v1.1")
    root.geometry("400x295")
    root.resizable(False, False)

    style = ttk.Style(root)
    style.theme_use('clam')

    frm = ttk.Frame(root, padding=15)
    frm.pack(fill="both", expand=True)
    frm.columnconfigure(0, weight=0, minsize=120)  # Fixed width for labels
    frm.columnconfigure(1, weight=1)  # Flexible width for inputs

    # Row 0: Click Button
    ttk.Label(frm, text="Click Button:").grid(row=0, column=0, sticky='w', pady=8)
    click_var = tk.StringVar(value=config['click_button'])
    click_combo = ttk.Combobox(frm, textvariable=click_var, values=["left", "right"], state="readonly", width=15)
    click_combo.grid(row=0, column=1, sticky='ew', padx=(10, 0))

    def on_click_button_change(event):
        config['click_button'] = click_var.get()
        auto_save_and_restart()
        cps_label.config(text=update_cps_label_text())

    click_combo.bind('<<ComboboxSelected>>', on_click_button_change)

    # Row 1: Click Mode
    ttk.Label(frm, text="Click Mode:").grid(row=1, column=0, sticky='w', pady=8)
    click_mode_var = tk.StringVar(value=config['click_mode'])
    mode_combo = ttk.Combobox(frm, textvariable=click_mode_var, values=["hold", "toggle", "burst"], state="readonly", width=15)
    mode_combo.grid(row=1, column=1, sticky='ew', padx=(10, 0))

    def on_click_mode_change(event):
        config['click_mode'] = click_mode_var.get()
        auto_save_and_restart()
        update_cps_burst_fields()

    mode_combo.bind('<<ComboboxSelected>>', on_click_mode_change)
    
    # Row 2: CPS / Burst
    cps_label_widget = ttk.Label(frm, text="CPS (Clicks/s):", anchor='w')
    cps_label_widget.grid(row=2, column=0, sticky='w', pady=9)

    cps_burst_frame = ttk.Frame(frm)
    cps_burst_frame.grid(row=2, column=1, sticky='ew', padx=(10, 0))

    cps_var = tk.IntVar(value=config['cps'])
    burst_count_var = tk.IntVar(value=config['burst_count'])
    burst_delay_var = tk.IntVar(value=config['burst_delay_ms'])

    cps_spin = ttk.Spinbox(cps_burst_frame, from_=1, to=100, textvariable=cps_var, width=10)
    burst_count_spin = ttk.Spinbox(cps_burst_frame, from_=1, to=100, textvariable=burst_count_var, width=8)
    burst_delay_spin = ttk.Spinbox(cps_burst_frame, from_=1, to=1000, textvariable=burst_delay_var, width=8)

    delay_label = ttk.Label(cps_burst_frame, text="Delay (ms):")

    def on_cps_change(event=None):
        try:
            value = int(cps_spin.get())
            if value < 1:
                value = 1
            cps_var.set(value)
            config['cps'] = value
            auto_save_and_restart()
        except ValueError:
            cps_var.set(config['cps'])

    def on_burst_count_change(event=None):
        try:
            value = int(burst_count_spin.get())
            if value < 1:
                value = 1
            burst_count_var.set(value)
            config['burst_count'] = value
            auto_save_and_restart()
        except ValueError:
            burst_count_var.set(config['burst_count'])

    def on_burst_delay_change(event=None):
        try:
            value = int(burst_delay_spin.get())
            if value < 1:
                value = 1
            burst_delay_var.set(value)
            config['burst_delay_ms'] = value
            auto_save_and_restart()
        except ValueError:
            burst_delay_var.set(config['burst_delay_ms'])

    cps_spin.bind('<FocusOut>', on_cps_change)
    cps_spin.bind('<Return>', on_cps_change)
    
    burst_count_spin.bind('<FocusOut>', on_burst_count_change)
    burst_count_spin.bind('<Return>', on_burst_count_change)

    burst_delay_spin.bind('<FocusOut>', on_burst_delay_change)
    burst_delay_spin.bind('<Return>', on_burst_delay_change)

    # Row 3: Trigger Key
    ttk.Label(frm, text="Trigger Key:").grid(row=3, column=0, sticky='w', pady=12)

    trigger_frame = ttk.Frame(frm)
    trigger_frame.grid(row=3, column=1, sticky='ew', padx=(10, 0))
    trigger_frame.columnconfigure(0, weight=1)

    trigger_display_widget = ttk.Label(trigger_frame, text=config['trigger_key'].upper(),
                                       relief='sunken', anchor='center', padding=6,
                                       background='white', width=15)
    trigger_display_widget.grid(row=0, column=0, sticky='ew')

    def wait_for_trigger():
        global waiting_for_trigger
        waiting_for_trigger = True
        trigger_display_widget.config(text="Press key/mouse...", width=15)

    ttk.Button(trigger_frame, text="Set", command=wait_for_trigger, width=8).grid(
        row=0, column=1, padx=(5, 0))

    # Row 4: CPS Test Area
    test_frame = ttk.Frame(frm, relief="raised", borderwidth=2, padding=10)
    test_frame.grid(row=4, column=0, columnspan=2, sticky="ew", pady=9)
    test_frame.columnconfigure(0, weight=1)

    test_area_frame = ttk.Frame(test_frame)
    test_area_frame.grid(row=1, column=0, columnspan=2, sticky="ew")
    test_area_frame.columnconfigure(0, weight=1)

    cps_label = ttk.Label(test_area_frame, text=update_cps_label_text(),
                          anchor='center', padding=15, relief="groove", cursor="hand2")
    cps_label.grid(row=0, column=0, sticky='ew')
    cps_label.bind("<Button-1>", on_test_click)
    cps_label.bind("<Button-3>", on_test_click)

    def reset_button_click():
        reset_test_cps()
        cps_label.config(text=update_cps_label_text())

    reset_btn = ttk.Button(test_area_frame, text="Reset", command=reset_button_click, width=8)
    reset_btn.grid(row=0, column=1, padx=(5, 0), sticky='ns')

    update_cps_burst_fields()

    root.protocol("WM_DELETE_WINDOW", lambda: [stop_all_listeners(), root.destroy()])

    # Row 5: Credit Frame
    credit_frame = ttk.Frame(frm)
    credit_frame.grid(row=5, column=0, columnspan=2, sticky='ew', pady=(0, 0))
    credit_frame.columnconfigure(0, weight=1)

    def open_github(event=None):
        webbrowser.open_new("https://github.com/fechl")

    credit_label = ttk.Label(credit_frame, text="github.com/fechl", foreground="blue", cursor="hand2", anchor='center', font=('Segoe UI', 10, 'underline'))
    credit_label.grid(row=0, column=0, sticky='ew')
    credit_label.bind("<Button-1>", open_github)

    root.mainloop()

if __name__ == "__main__":
    build_ui()