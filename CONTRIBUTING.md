# Contributing to chatCAT

First off, thank you for considering contributing to chatCAT!

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [How Can I Contribute?](#how-can-i-contribute)
- [Development Setup](#development-setup)
- [Pull Request Process](#pull-request-process)
- [Style Guidelines](#style-guidelines)
- [Adding Platform Support](#adding-platform-support)

## Code of Conduct

This project and everyone participating in it is governed by our commitment to creating a welcoming environment. Please be respectful and constructive in all interactions.

## How Can I Contribute?

### Reporting Bugs

Before creating bug reports, please check existing issues to avoid duplicates.

When creating a bug report, include:

- **Clear title** describing the issue
- **Steps to reproduce** the problem
- **Expected behaviour** vs **actual behaviour**
- **Platform/browser** information
- **Console logs** (F12 → Console, filter by "chatCAT")
- **Screenshots** if applicable

### Suggesting Features

Feature suggestions are welcome! Please:

- Check if the feature has already been suggested
- Provide a clear description of the feature
- Explain why it would be useful
- Consider how it fits with existing functionality

### Adding Platform Support

Want to add support for a new AI platform? See [Adding Platform Support](#adding-platform-support) below.

### Improving Documentation

Documentation improvements are always welcome:

- Fix typos or unclear explanations
- Add examples
- Improve installation instructions
- Translate documentation

## Development Setup

### Prerequisites

- Python 3.8+
- A browser with Tampermonkey installed
- Git

### Setup Steps

1. **Fork the repository** on GitHub

2. **Clone your fork**:
   ```bash
   git clone https://github.com/YOUR_USERNAME/chatCAT.git
   cd chatCAT
   ```

3. **Create a branch**:
   ```bash
   git checkout -b feature/your-feature-name
   ```

4. **Start the server**:
   ```bash
   python chatcat_server.py
   ```

5. **Install the userscript** in Tampermonkey (see INSTALLATION.md)

6. **Make your changes**

7. **Test thoroughly** on all affected platforms

## Pull Request Process

1. **Update documentation** if you've changed functionality

2. **Update CHANGELOG.md** with your changes under "Unreleased"

3. **Test your changes**:
   - Test on at least 2-3 platforms
   - Verify no console errors
   - Check that existing functionality still works

4. **Commit with clear messages**:
   ```bash
   git commit -m "Add support for NewPlatform"
   git commit -m "Fix: Message role detection on Gemini"
   ```

5. **Push to your fork**:
   ```bash
   git push origin feature/your-feature-name
   ```

6. **Create a Pull Request**:
   - Use a clear title
   - Reference any related issues
   - Describe what changes you made and why

## Style Guidelines

### Python (Server)

- Follow PEP 8 style guide
- Use meaningful variable names
- Add docstrings to functions
- Keep functions focused and small

```python
def get_chat_by_id(self, chat_id):
    """
    Retrieve a chat by its ID.
    
    Args:
        chat_id: Integer ID of the chat
        
    Returns:
        Tuple containing chat data or None if not found
    """
    # Implementation
```

### JavaScript (Userscript)

- Use `const` and `let`, avoid `var`
- Use meaningful function and variable names
- Add comments for complex logic
- Use template literals for string building

```javascript
// Good
const platformName = detectPlatform();
const messages = captureFunctions[platformName]();

// Avoid
var p = detectPlatform();
var m = captureFunctions[p]();
```

### Commit Messages

- Use present tense: "Add feature" not "Added feature"
- Use imperative mood: "Fix bug" not "Fixes bug"
- Keep first line under 50 characters
- Add details in body if needed

```
Add DeepSeek platform support

- Add @match rule for chat.deepseek.com
- Implement capture function using ds-message class
- User messages identified by d29f3d7d class
```

## Adding Platform Support

Want to add support for a new AI platform? Follow these steps:

### 1. Research the Platform

Run this DOM inspection script in the browser console on the platform:

```javascript
// DOM Inspector for chatCAT
console.log('=== DOM INSPECTION ===');

const selectors = [
    '[class*="user"]', '[class*="User"]',
    '[class*="human"]', '[class*="Human"]',
    '[class*="assistant"]', '[class*="Assistant"]',
    '[class*="bot"]', '[class*="Bot"]',
    '[class*="message"]', '[class*="Message"]',
    '[class*="response"]', '[class*="Response"]'
];

selectors.forEach(sel => {
    const els = document.querySelectorAll(sel);
    if (els.length > 0 && els.length < 50) {
        console.log(`${sel}: ${els.length} found`);
        console.log(`  CLASS: "${els[0].className}"`);
        console.log(`  TEXT: "${els[0].textContent.substring(0, 60)}..."`);
    }
});
```

### 2. Add the @match Rule

In the userscript header:

```javascript
// @match        https://newplatform.com/*
```

### 3. Add Platform Detection

In `detectPlatform()`:

```javascript
if (hostname.includes('newplatform.com')) return 'newplatform';
```

### 4. Create Capture Function

Add to `captureFunctions` object:

```javascript
newplatform: () => {
    const messages = [];
    
    // Find message elements
    document.querySelectorAll('.message-selector').forEach(el => {
        const text = el.textContent.trim();
        if (!text || text.length < 3) return;
        
        // Determine if user or assistant
        const isUser = /* your detection logic */;
        
        messages.push({
            role: isUser ? 'user' : 'assistant',
            content: text,
            position: el.getBoundingClientRect().top
        });
    });
    
    // Sort by position
    messages.sort((a, b) => a.position - b.position);
    return messages.map(m => ({ role: m.role, content: m.content }));
},
```

### 5. Test Thoroughly

- Test with single message exchanges
- Test with long conversations
- Test that user/assistant roles are correct
- Verify no duplicate captures
- Check for console errors

### 6. Update Documentation

- Add platform to README.md supported platforms table
- Add to CHANGELOG.md
- Update any relevant documentation

## Questions?

Feel free to open an issue with the "question" label if you need help!

---

Thank you for contributing to chatCAT! 🐱
