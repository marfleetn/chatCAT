# 📦 chatCAT Installation Guide

This guide will walk you through setting up chatCAT on your system.

## Table of Contents

1. [System Requirements](#system-requirements)
2. [Installing Python](#installing-python)
3. [Installing Tampermonkey](#installing-tampermonkey)
4. [Setting Up chatCAT](#setting-up-chatcat)
5. [Running the Server](#running-the-server)
6. [Installing the Userscript](#installing-the-userscript)
7. [Verifying Installation](#verifying-installation)
8. [Auto-Start on Boot (Optional)](#auto-start-on-boot-optional)
9. [Troubleshooting](#troubleshooting)

---

## System Requirements

- **Operating System**: Windows 10/11, macOS 10.14+, or Linux
- **Python**: 3.8 or higher
- **Browser**: Chrome, Firefox, Edge, or any Chromium-based browser
- **Disk Space**: ~50MB (plus space for your conversation database)
- **RAM**: 512MB minimum

---

## Installing Python

### Windows

1. Download Python from [python.org](https://www.python.org/downloads/)
2. Run the installer
3. **Important**: Check "Add Python to PATH" during installation
4. Click "Install Now"
5. Verify installation:
   ```cmd
   python --version
   ```

### macOS

Python 3 may already be installed. Check with:
```bash
python3 --version
```

If not installed, use Homebrew:
```bash
brew install python
```

Or download from [python.org](https://www.python.org/downloads/macos/)

### Linux (Ubuntu/Debian)

```bash
sudo apt update
sudo apt install python3 python3-pip
```

### Linux (Fedora)

```bash
sudo dnf install python3 python3-pip
```

---

## Installing Tampermonkey

Tampermonkey is a browser extension that runs userscripts.

### Chrome
1. Visit the [Chrome Web Store](https://chrome.google.com/webstore/detail/tampermonkey/dhdgffkkebhmkfjojejmpbldmpobfkfo)
2. Click "Add to Chrome"
3. Confirm by clicking "Add extension"

### Firefox
1. Visit [Firefox Add-ons](https://addons.mozilla.org/en-US/firefox/addon/tampermonkey/)
2. Click "Add to Firefox"
3. Confirm by clicking "Add"

### Microsoft Edge
1. Visit the [Edge Add-ons](https://microsoftedge.microsoft.com/addons/detail/tampermonkey/iikmkjmpaadaobahmlepeloendndfphd)
2. Click "Get"
3. Confirm by clicking "Add extension"

### Safari
1. Visit the [Mac App Store](https://apps.apple.com/app/tampermonkey/id1482490089)
2. Click "Get" then "Install"
3. Enable in Safari → Preferences → Extensions

---

## Setting Up chatCAT

### Option 1: Download ZIP

1. Go to the [chatCAT releases page](https://github.com/marfleetn/chatCAT/releases)
2. Download the latest release ZIP
3. Extract to your preferred location (e.g., `C:\chatCAT` or `~/chatCAT`)

### Option 2: Clone with Git

```bash
git clone https://github.com/marfleetn/chatCAT.git
cd chatCAT
```

### Directory Structure

After setup, you should have:
```
chatCAT/
├── chatcat_server.py       # The server file
├── chatCAT_userscript.js   # The userscript file
├── README.md
└── ...
```

---

## Running the Server

### Starting the Server

Navigate to the chatCAT directory and run:

**Windows (Command Prompt)**:
```cmd
cd C:\path\to\chatCAT
python chatcat_server.py
```

**Windows (PowerShell)**:
```powershell
cd C:\path\to\chatCAT
python chatcat_server.py
```

**macOS/Linux**:
```bash
cd ~/path/to/chatCAT
python3 chatcat_server.py
```

### Successful Start

You should see:
```
═══════════════════════════════════════════════
         chatCAT v2.4 - MS-DOS Edition
═══════════════════════════════════════════════

■ Dashboard: http://localhost:8765
■ API Endpoint: http://localhost:8765/api/add

✓ Database initialised: ai_chats.db

▶ Press Ctrl+C to stop the server.
```

### Accessing the Dashboard

Open your browser and go to: **http://localhost:8765**

---

## Installing the Userscript

### Step 1: Open Tampermonkey Dashboard

1. Click the Tampermonkey icon in your browser toolbar
2. Click "Dashboard"

### Step 2: Create New Script

1. Click the "+" tab or "Create a new script"
2. Delete any default code in the editor

### Step 3: Paste the Script

1. Open `chatCAT_userscript.js` in a text editor
2. Select all (`Ctrl+A` / `Cmd+A`)
3. Copy (`Ctrl+C` / `Cmd+C`)
4. Paste into Tampermonkey editor (`Ctrl+V` / `Cmd+V`)

### Step 4: Save

1. Press `Ctrl+S` / `Cmd+S` to save
2. Or click File → Save

### Step 5: Verify Installation

1. Go to Tampermonkey Dashboard → Installed Userscripts
2. You should see "chatCAT - MS-DOS Theme v2.4.0"
3. Ensure it's enabled (toggle should be ON)

---

## Verifying Installation

### Test the Setup

1. **Ensure server is running** (you should see the chatCAT output in terminal)

2. **Visit a supported platform** (e.g., https://claude.ai)

3. **Look for the indicator**:
   - A small green box should appear in the bottom-right corner
   - It should say "chatCAT" with "0 captured"

4. **Have a conversation**:
   - Send a message and wait for a response
   - The indicator should update to "1 captured"

5. **Check the dashboard**:
   - Click the chatCAT indicator (or go to http://localhost:8765)
   - Your conversation should appear in the search results

### Troubleshooting Checklist

- [ ] Python installed and in PATH
- [ ] Server running without errors
- [ ] Tampermonkey installed and enabled
- [ ] Userscript installed and enabled
- [ ] On a supported platform
- [ ] No browser console errors (F12 → Console)

---

## Auto-Start on Boot (Optional)

### Windows

1. Create a batch file `start_chatcat.bat`:
   ```batch
   @echo off
   cd /d C:\path\to\chatCAT
   python chatcat_server.py
   ```

2. Press `Win+R`, type `shell:startup`, press Enter
3. Create a shortcut to `start_chatcat.bat` in this folder

### macOS

1. Create a launch agent file:
   ```bash
   nano ~/Library/LaunchAgents/com.chatcat.server.plist
   ```

2. Add this content:
   ```xml
   <?xml version="1.0" encoding="UTF-8"?>
   <!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
   <plist version="1.0">
   <dict>
       <key>Label</key>
       <string>com.chatcat.server</string>
       <key>ProgramArguments</key>
       <array>
           <string>/usr/bin/python3</string>
           <string>/Users/YOURUSERNAME/chatCAT/chatcat_server.py</string>
       </array>
       <key>RunAtLoad</key>
       <true/>
       <key>WorkingDirectory</key>
       <string>/Users/YOURUSERNAME/chatCAT</string>
   </dict>
   </plist>
   ```

3. Load it:
   ```bash
   launchctl load ~/Library/LaunchAgents/com.chatcat.server.plist
   ```

### Linux (systemd)

1. Create a service file:
   ```bash
   sudo nano /etc/systemd/system/chatcat.service
   ```

2. Add this content:
   ```ini
   [Unit]
   Description=chatCAT Server
   After=network.target

   [Service]
   Type=simple
   User=YOURUSERNAME
   WorkingDirectory=/home/YOURUSERNAME/chatCAT
   ExecStart=/usr/bin/python3 chatcat_server.py
   Restart=on-failure

   [Install]
   WantedBy=multi-user.target
   ```

3. Enable and start:
   ```bash
   sudo systemctl enable chatcat
   sudo systemctl start chatcat
   ```

---

## Troubleshooting

### "python" is not recognized

**Windows**: Python wasn't added to PATH. Reinstall Python and check "Add Python to PATH".

**macOS/Linux**: Try `python3` instead of `python`.

### Port 8765 already in use

Another application is using this port. Either:
1. Close the other application
2. Change the port in `chatcat_server.py`:
   ```python
   def run_server(port=8766):  # Change to different port
   ```
   And update the userscript:
   ```javascript
   const SERVER_URL = 'http://localhost:8766/api/add';
   ```

### Indicator not showing

1. Check Tampermonkey icon - does it show "1" indicating a script is running?
2. Open browser console (F12) and filter by "chatCAT"
3. Look for any error messages
4. Try disabling other extensions temporarily

### Conversations not captured

1. Ensure server is running
2. Check browser console for `[chatCAT] Chat captured successfully` messages
3. If you see connection errors, the server might not be running

### Database locked error

This can happen if multiple server instances are running. Close all terminal windows and restart with a single server instance.

---

## Getting Help

- **GitHub Issues**: [Report a bug](https://github.com/marfleetn/chatCAT/issues)
- **Discussions**: [Ask questions](https://github.com/marfleetn/chatCAT/discussions)

---

<p align="center">
  <b>Happy cataloguing! 🐱</b>
</p>
