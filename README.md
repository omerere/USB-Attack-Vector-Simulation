# USB Attack Vector Simulation 


## Project Overview
This project simulates a full-lifecycle Red Team operation focusing on physical access vectors.
The goal is to demonstrate how an adversary can bypass network firewalls using a weaponized USB drive, maintain persistence, and automate the intelligence gathering process using AI.
## Compatibility
- **Operating System:** Windows 10 / 11 (64-bit)
- **Note:** This is a native Windows application. It is not currently supported on macOS or Linux.

**The Attack Scenario:**
1.  **Infiltration (The Honey Trap):** A USB drive labeled "CRYPTO WALLET" is dropped in a target location, such as Binance store. It contains a payload disguised as `Wallet_App.exe`.
2.  **Infection:** When the victim opens the file, the malware installs silently to the Windows Startup folder while displaying a fake "Wallet has been disabled" error to lower suspicion.
3.  **Exfiltration (The Chain):** To remain stealthy, the malware streams encrypted logs to an intermediate "Dead Drop" email account.
4.  **Intelligence (The AI):** Once a day, the attacker's server automatically aggregates these logs and uses **Google Gemini AI** to extract high-value credentials (passwords/users) and generate a clean intelligence report.

## Architecture: 
This project implements 3-Tier Exfiltration Architecture to hide the attacker's identity:



* **Tier 1: Raw Log Sender**
    * **Role:** The "Sender" account embedded in the malware.
    * **Security:** Disposable. If the malware is reverse-engineered, the victim only finds this empty shell account.
* **Tier 2: Raw Log Receiver**
    * **Role:** The "Receiver" / "Dead Drop".
    * **Security:** Never accessed directly by the malware. It acts as a holding tank for raw data logs.
* **Tier 3: Processed Data Receiver**
    * **Role:** The Attacker's personal secure email.
    * **Security:** Completely air-gapped from the victim. Receives only the final, AI-processed report and a single file with the daily logs.

## Technical Capabilities

### 1. Payload & Persistence (`keylogger.py`, `deployment.py`)
* **Hardware Hooking:** Uses `ctypes` to interact with low-level Windows APIs (`user32.dll`) for capturing raw input.
* **Smart Normalization:** Detects active keyboard layouts (Hebrew/English toggling) and Shift/Caps Lock states.
* **Registry Persistence:** Replicates itself to `AppData\Roaming\Microsoft\Windows\Start Menu\Programs\Startup` for reboot survival.

### 2. Email Service (`email_service.py`)
* **Generic Service:** Implements `EmailService` class.
* **TLS Encryption:** All traffic is transmitted via SMTP/SSL (Port 465) to bypass basic packet sniffing.

### 3. AI Analysis Module (`log_analyzer.py`)
* **Automated Aggregation:** Connects to the raw logs receiver mail via IMAP, fetching only logs created today.
* **AI Integration:** Uses Google Gemini to parse lines of raw keystrokes.
* **Credential Harvesting:** The AI filters out noise (backspaces, navigation keys) and extracts only potential usernames, passwords, and URLs.

## Project Structure

| File | Module | Description |
| :--- | :--- | :--- |
| `main.py` | **Orchestrator** | Entry point. Manages the malware lifecycle (Looping, Logging, Wiping Evidence). |
| `deployment.py` | **Loader** | Handles installation, persistence, and the Social Engineering "Fake Error" UI. |
| `keylogger.py` | **Payload** | Captures and interprets hardware input signals. |
| `email_service.py` | **Service** | Generic SMTP client used by both the Malware (for logs) and the Analyzer (for reports). |
| `log_analyzer.py` | **Intelligence** | Post-exploitation tool. Fetches logs, runs AI analysis, and emails the Master Report. |
| `config.py` | **Configuration** | Centralized credentials for the 3-Email Chain and API Keys. |

## Setup & Usage

### Prerequisites
* Python 3.10+
* **Dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

### 1. Configuration & Credentials

Before running the software, you must initialize the configuration file.

**IMPORTANT:** You must enable "2-Step Verification" and generate an "App Password" for the email accounts used below.
* **Official Guide:** [How to generate an App Password](https://support.google.com/accounts/answer/185833)

1.  **Initialize the Config File:**
    Rename `config.py.example` to `config.py`.

2.  **Edit Credentials:**
    Open `config.py` in your text editor and configure the following variables:

    * **`RAW_LOG_SENDER` :** The Gmail account embedded in the malware to send logs. (Requires App Password).
    * **`RAW_LOG_RECEIVER` :** The intermediate "Dead Drop" account that receives raw logs.
    * **`FINAL_REPORT_RECEIVER` :** Your personal secure email where the final Intelligence Report will be sent.
    * **`API_KEY`:** Your Google Gemini API Key (Required for log analysis).

### 2. Build the the malware
Compile the script into a standalone executable for the USB drive:
```bash
pyinstaller --onefile --noconsole --name="Crypto_Wallet" --icon="bitcoin.ico" main.py
```

### 3. Run the Analysis (The Attacker)
This script runs on your machine (not the victim's). Run it manually (e.g., once a day) to process the logs collected in the raw logs receiver mail:
```bash
python log_analyzer.py
```