# chatCAT

**Organise Your AI Conversations**

[![Version](https://img.shields.io/badge/version-2.4.0-green.svg)](https://github.com/marfleetn/chatCAT/releases)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.8+-yellow.svg)](https://www.python.org/)

chatCAT is a sophisticated AI conversation cataloguing system that automatically captures, organises, and searches your conversations across multiple AI platforms. Never lose an important AI conversation again!

![chatCAT Dashboard](docs/images/dashboard-preview.png)

## ✨ Features

- **🔄 Auto-Capture**: Automatically captures conversations in real-time as you chat
- **🔍 Advanced Search**: Full-text search with relevance ranking and term highlighting
- **🏷️ Tagging System**: Colour-coded tags to organise your conversations
- **📝 Notes**: Add personal notes to any conversation
- **📊 Dashboard**: MS-DOS inspired retro interface with statistics
- **🌐 Multi-Platform**: Supports 9 major AI platforms

## 🤖 Supported Platforms

| Platform | URL | Status |
|----------|-----|--------|
| Claude | claude.ai | ✅ Supported |
| ChatGPT | chatgpt.com | ✅ Supported |
| Gemini | gemini.google.com | ✅ Supported |
| Grok | grok.com | ✅ Supported |
| DeepSeek | chat.deepseek.com | ✅ Supported |
| Perplexity | perplexity.ai | ✅ Supported |
| Poe | poe.com | ✅ Supported |
| ChatLLM | apps.abacus.ai | ✅ Supported |
| Manus | manus.im | ✅ Supported |

## 🛠️ Installation

### Prerequisites

- **Python 3.8+** - [Download Python](https://www.python.org/downloads/)
- **Tampermonkey** browser extension - [Chrome](https://chrome.google.com/webstore/detail/tampermonkey/dhdgffkkebhmkfjojejmpbldmpobfkfo) | [Firefox](https://addons.mozilla.org/en-US/firefox/addon/tampermonkey/) | [Edge](https://microsoftedge.microsoft.com/addons/detail/tampermonkey/iikmkjmpaadaobahmlepeloendndfphd)

### Quick Start

#### 1. Clone the Repository

```bash
git clone https://github.com/marfleetn/chatCAT.git
cd chatCAT
```

#### 2. Start the Server

```bash
python chatcat_server.py
```

You should see:
```
═══════════════════════════════════════════════
         chatCAT v2.4 - MS-DOS Edition
═══════════════════════════════════════════════

■ Dashboard: http://localhost:8765
■ API Endpoint: http://localhost:8765/api/add

▶ Press Ctrl+C to stop the server.
```

#### 3. Install the Userscript

1. Open Tampermonkey in your browser
2. Click "Create a new script"
3. Delete any default content
4. Copy and paste the contents of `chatCAT_userscript.js`
5. Press `Ctrl+S` to save

#### 4. Start Chatting!

1. Visit any supported AI platform (e.g., claude.ai)
2. You should see the green **chatCAT** indicator in the bottom-right corner
3. Have a conversation - it will be automatically captured
4. Click the indicator to open the dashboard and search your conversations

## 📖 Usage

### Dashboard

Access the dashboard at `http://localhost:8765` while the server is running.

- **Search**: Enter keywords to search across all your conversations
- **Filter by Platform**: Select specific AI platforms to search
- **Date Range**: Filter conversations by date
- **View Full Chat**: Click any result to see the complete conversation
- **Add Notes**: Add personal notes to any conversation
- **Manage Tags**: Create and assign colour-coded tags

### Indicator

The floating chatCAT indicator shows:
- Number of conversations captured in the current session
- Click to open the dashboard
- Drag to reposition (hold for 0.5s then drag)

### Keyboard Shortcuts

- `Enter` in search box: Perform search
- `Escape`: Close modal dialogs

## 🗂️ Project Structure

```
chatCAT/
├── chatcat_server.py      # Python server & web dashboard
├── chatCAT_userscript.js  # Tampermonkey userscript
├── ai_chats.db            # SQLite database (created on first run)
├── README.md              # This file
├── LICENSE                # MIT License
├── CHANGELOG.md           # Version history
├── CONTRIBUTING.md        # Contribution guidelines
└── docs/
    └── images/            # Documentation images
```

## ⚙️ Configuration

### Server Configuration

Edit `chatcat_server.py` to change:

```python
DB_FILE = 'ai_chats.db'  # Database file location
```

Server runs on port `8765` by default. To change:

```python
def run_server(port=8765):  # Change port here
```

### Userscript Configuration

Edit `chatCAT_userscript.js` to change:

```javascript
const SERVER_URL = 'http://localhost:8765/api/add';  // Server URL
const CHECK_INTERVAL = 3000;  // Capture check interval (ms)
```

## 🔧 Troubleshooting

### Indicator not appearing

1. Check Tampermonkey is enabled
2. Verify the script is enabled for the current site
3. Check browser console for errors (F12 → Console)
4. Try refreshing the page

### Conversations not being captured

1. Ensure the server is running
2. Check the browser console for `[chatCAT]` messages
3. Verify the platform is supported
4. Try disabling other userscripts that might conflict

### Server won't start

1. Check Python is installed: `python --version`
2. Ensure port 8765 is not in use
3. Check for error messages in the terminal

### Database errors

If you encounter database errors, you can:
1. Stop the server
2. Delete `ai_chats.db` (⚠️ this will delete all saved conversations)
3. Restart the server (a fresh database will be created)

## 🤝 Contributing

Contributions are welcome! Please read [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

### Development Setup

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/amazing-feature`
3. Make your changes
4. Test thoroughly on multiple platforms
5. Commit: `git commit -m 'Add amazing feature'`
6. Push: `git push origin feature/amazing-feature`
7. Open a Pull Request

## 📜 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgements

- Inspired by the need to organise AI conversations across multiple platforms
- MS-DOS aesthetic for that retro computing feel
- Built with Python, JavaScript, and SQLite

## 📬 Contact

- **Author**: Nick Marfleet
- **Issues**: [GitHub Issues](https://github.com/marfleetn/chatCAT/issues)

---

<p align="center">
  <b>chatCAT</b> - Because every conversation deserves to be remembered 🐱
</p>
