// ==UserScript==
// @name         chatCAT - MS-DOS Theme v2.4.0
// @namespace    http://tampermonkey.net/
// @version      2.4.0
// @description  AI conversation cataloguing with MS-DOS aesthetic - Added Grok & DeepSeek
// @author       Nick Marfleet
// @match        https://claude.ai/*
// @match        https://chatgpt.com/*
// @match        https://gemini.google.com/*
// @match        https://grok.com/*
// @match        https://chat.deepseek.com/*
// @match        https://manus.im/*
// @match        https://apps.abacus.ai/*
// @match        https://www.perplexity.ai/*
// @match        https://poe.com/*
// @grant        GM_xmlhttpRequest
// @grant        GM_openInTab
// @grant        GM_addStyle
// @grant        unsafeWindow
// @run-at       document-idle
// @connect      localhost
// ==/UserScript==

(function() {
    'use strict';

    // Configuration
    const SERVER_URL = 'http://localhost:8765/api/add';
    const CHECK_INTERVAL = 3000;
    const INDICATOR_CHECK_INTERVAL = 2000;
    
    // MS-DOS Color Scheme
    const COLORS = {
        bgDark: '#3C3C3C',
        bgDarker: '#2A2A2A',
        bgLighter: '#4A4A4A',
        textPrimary: '#FFFFFF',
        textSecondary: '#CCCCCC',
        accentGreen: '#00FF00',
        accentDim: '#00AA00',
        borderWhite: '#FFFFFF',
        borderGray: '#666666',
        errorRed: '#FF4444'
    };

    // State
    let indicator = null;
    let titleElement = null;
    let countElement = null;
    let lastCapturedMessage = '';
    let captureCount = 0;
    let initAttempts = 0;
    const MAX_INIT_ATTEMPTS = 10;

    // Debug logging
    function log(message, type = 'info') {
        const prefix = '[chatCAT]';
        const styles = {
            info: 'color: #00FF00',
            warn: 'color: #FFAA00',
            error: 'color: #FF4444',
            success: 'color: #00FF00; font-weight: bold'
        };
        console.log(`%c${prefix} ${message}`, styles[type] || styles.info);
    }

    // Inject styles using GM_addStyle (bypasses Trusted Types)
    function injectStyles() {
        const css = `
            #chatcat-indicator {
                position: fixed !important;
                bottom: 20px !important;
                right: 20px !important;
                width: 120px !important;
                height: 70px !important;
                background: ${COLORS.bgDarker} !important;
                color: ${COLORS.accentGreen} !important;
                border: 2px solid ${COLORS.borderWhite} !important;
                padding: 12px !important;
                font-family: 'Courier New', Consolas, Monaco, monospace !important;
                font-size: 11px !important;
                z-index: 2147483647 !important;
                cursor: pointer !important;
                box-shadow: 0 0 15px rgba(0, 255, 0, 0.3) !important;
                text-align: center !important;
                display: flex !important;
                flex-direction: column !important;
                justify-content: center !important;
                align-items: center !important;
                text-shadow: 0 0 10px rgba(0, 255, 0, 0.5) !important;
                user-select: none !important;
                pointer-events: auto !important;
                visibility: visible !important;
                opacity: 1 !important;
                transform: translateZ(0) !important;
            }
            
            #chatcat-indicator:hover {
                background: ${COLORS.accentGreen} !important;
                color: ${COLORS.bgDark} !important;
                box-shadow: 0 0 25px rgba(0, 255, 0, 0.8) !important;
                text-shadow: none !important;
            }
            
            #chatcat-indicator.chatcat-dragging {
                cursor: move !important;
                border-color: ${COLORS.accentGreen} !important;
                border-width: 3px !important;
            }
            
            .chatcat-title {
                font-size: 12px !important;
                font-weight: 700 !important;
                letter-spacing: 2px !important;
            }
            
            .chatcat-count {
                font-size: 10px !important;
                margin-top: 2px !important;
            }
            
            .chatcat-notification {
                position: fixed !important;
                top: 20px !important;
                right: 20px !important;
                padding: 15px 20px !important;
                font-family: 'Courier New', Consolas, Monaco, monospace !important;
                font-size: 13px !important;
                font-weight: 600 !important;
                z-index: 2147483647 !important;
                box-shadow: 0 0 20px rgba(0, 255, 0, 0.5) !important;
                pointer-events: none !important;
            }
        `;
        
        // Use GM_addStyle which bypasses CSP/Trusted Types
        if (typeof GM_addStyle === 'function') {
            try {
                GM_addStyle(css);
                log('Styles injected via GM_addStyle');
            } catch (e) {
                log('GM_addStyle failed: ' + e.message, 'warn');
            }
        }
    }

    // Detect current platform
    function detectPlatform() {
        const hostname = window.location.hostname;
        if (hostname.includes('claude.ai')) return 'claude';
        if (hostname.includes('chatgpt.com')) return 'chatgpt';
        if (hostname.includes('gemini.google.com')) return 'gemini';
        if (hostname.includes('grok.com')) return 'grok';
        if (hostname.includes('chat.deepseek.com')) return 'deepseek';
        if (hostname.includes('manus.im')) return 'manus';
        if (hostname.includes('apps.abacus.ai')) return 'chatllm';
        if (hostname.includes('perplexity.ai')) return 'perplexity';
        if (hostname.includes('poe.com')) return 'poe';
        return 'unknown';
    }

    // Platform-specific capture functions
    const captureFunctions = {
        claude: () => {
            const messages = [];
            
            const selectors = [
                '[data-test-render-count]',
                '[class*="Message"]',
                '[class*="message"]',
                'div[class*="prose"]'
            ];
            
            let messageElements = [];
            for (const selector of selectors) {
                messageElements = document.querySelectorAll(selector);
                if (messageElements.length > 0) break;
            }
            
            messageElements.forEach(el => {
                const isUser = el.querySelector('[data-testid="user-message"]') !== null ||
                              el.closest('[data-testid="user-message"]') !== null ||
                              el.className.toLowerCase().includes('human') ||
                              el.className.toLowerCase().includes('user');
                
                // Get text content more carefully - exclude avatars and UI elements
                let textContent = '';
                
                const contentSelectors = [
                    '[data-testid="user-message"]',
                    '.prose',
                    '.markdown',
                    '[class*="message-content"]',
                    '[class*="MessageContent"]'
                ];
                
                let contentEl = null;
                for (const sel of contentSelectors) {
                    contentEl = el.querySelector(sel);
                    if (contentEl) break;
                }
                
                if (contentEl) {
                    const clone = contentEl.cloneNode(true);
                    
                    const removeSelectors = [
                        '[class*="avatar"]',
                        '[class*="Avatar"]',
                        '[class*="icon"]',
                        '[class*="Icon"]',
                        'button',
                        '[role="button"]',
                        '[class*="sr-only"]',
                        '[class*="screenreader"]'
                    ];
                    
                    removeSelectors.forEach(sel => {
                        clone.querySelectorAll(sel).forEach(e => e.remove());
                    });
                    
                    textContent = clone.textContent.trim();
                } else {
                    textContent = el.textContent.trim();
                }
                
                // Clean up UI text and common artifacts
                textContent = textContent
                    .replace(/^Copy(code)?/gi, '')
                    .replace(/Edit$/gi, '')
                    .replace(/^\d+\s*$/, '')
                    .replace(/^[A-Z]\s+/i, '')
                    .replace(/^(Copy|Edit|Share|Like|Dislike)\s*/gi, '')
                    .trim();
                
                if (textContent && textContent.length > 5) {
                    messages.push({
                        role: isUser ? 'user' : 'assistant',
                        content: textContent
                    });
                }
            });
            
            return messages;
        },
        
        chatgpt: () => {
            const messages = [];
            const messageElements = document.querySelectorAll('[data-message-author-role]');
            
            messageElements.forEach(el => {
                const role = el.getAttribute('data-message-author-role');
                let textContent = el.textContent.trim();
                textContent = textContent.replace(/^Copy(code)?/gi, '').trim();
                
                if (textContent && role) {
                    messages.push({
                        role: role === 'user' ? 'user' : 'assistant',
                        content: textContent
                    });
                }
            });
            
            return messages;
        },
        
        gemini: () => {
            const messages = [];
            const allMessages = [];
            
            // User selectors for Gemini
            const userSelectors = [
                '[class*="query-content"]',
                '[class*="user-query"]',
                '.query-text',
                'user-query'
            ];
            
            // AI selectors for Gemini
            const aiSelectors = [
                '[class*="model-response"]',
                '[class*="markdown"]',
                'model-response'
            ];
            
            userSelectors.forEach(selector => {
                try {
                    document.querySelectorAll(selector).forEach(el => {
                        const text = el.textContent.trim();
                        if (text && text.length > 3) {
                            allMessages.push({
                                role: 'user',
                                content: text,
                                position: el.getBoundingClientRect().top
                            });
                        }
                    });
                } catch (e) {}
            });
            
            aiSelectors.forEach(selector => {
                try {
                    document.querySelectorAll(selector).forEach(el => {
                        let text = el.textContent.trim();
                        // Remove "Show thinking" prefix if present
                        text = text.replace(/^Show thinking/i, '').trim();
                        if (text && text.length > 20) {
                            allMessages.push({
                                role: 'assistant',
                                content: text,
                                position: el.getBoundingClientRect().top
                            });
                        }
                    });
                } catch (e) {}
            });
            
            // Remove duplicates and sort by position
            const seen = new Set();
            const unique = allMessages.filter(m => {
                const key = m.content.substring(0, 100);
                if (seen.has(key)) return false;
                seen.add(key);
                return true;
            });
            
            unique.sort((a, b) => a.position - b.position);
            
            return unique.map(m => ({ role: m.role, content: m.content }));
        },
        
        grok: () => {
            const messages = [];
            
            // Grok uses message-bubble class, role determined by parent's items-end (user) vs items-start (AI)
            document.querySelectorAll('.message-bubble').forEach(el => {
                const text = el.textContent.trim();
                if (!text || text.length < 3) return;
                
                // Check parent for alignment class to determine role
                const parent = el.parentElement;
                let isUser = false;
                
                if (parent && parent.className) {
                    // User messages have items-end, AI messages have items-start
                    if (parent.className.includes('items-end')) {
                        isUser = true;
                    }
                }
                
                messages.push({
                    role: isUser ? 'user' : 'assistant',
                    content: text,
                    position: el.getBoundingClientRect().top
                });
            });
            
            // Sort by position and return
            messages.sort((a, b) => a.position - b.position);
            return messages.map(m => ({ role: m.role, content: m.content }));
        },
        
        deepseek: () => {
            const messages = [];
            
            // DeepSeek uses ds-message class
            // User messages have additional class 'd29f3d7d', AI messages don't
            document.querySelectorAll('.ds-message, [class*="ds-message"]').forEach(el => {
                const text = el.textContent.trim();
                if (!text || text.length < 3) return;
                
                const className = el.className || '';
                // User messages have the extra hash class 'd29f3d7d'
                const isUser = className.includes('d29f3d7d');
                
                messages.push({
                    role: isUser ? 'user' : 'assistant',
                    content: text,
                    position: el.getBoundingClientRect().top
                });
            });
            
            // Sort by position and return
            messages.sort((a, b) => a.position - b.position);
            return messages.map(m => ({ role: m.role, content: m.content }));
        },
        
        manus: () => {
            const messages = [];
            const allMsgs = document.querySelectorAll('[class*="message"], [class*="Message"]');
            
            allMsgs.forEach(el => {
                const className = el.className.toLowerCase();
                const text = el.textContent.trim();
                
                if (!text || text.length < 3) return;
                
                const isUser = className.includes('user') || 
                              className.includes('human') ||
                              className.includes('sent');
                
                const isAssistant = className.includes('assistant') ||
                                   className.includes('bot') ||
                                   className.includes('ai') ||
                                   className.includes('received');
                
                if (isUser || isAssistant) {
                    messages.push({
                        role: isUser ? 'user' : 'assistant',
                        content: text
                    });
                }
            });
            
            return messages;
        },
        
        chatllm: () => {
            const messages = [];
            
            // ChatLLM (apps.abacus.ai) uses flex containers
            // User messages: parent has 'justify-end' (right-aligned)
            // AI messages: parent has 'flex' without 'justify-end' (left-aligned)
            // Content is in elements with 'prose' and 'markdown' classes
            
            // Find all message containers - look for the prose/markdown content
            document.querySelectorAll('.prose.markdown, [class*="prose"][class*="markdown"]').forEach(el => {
                const text = el.textContent.trim();
                if (!text || text.length < 5) return;
                
                // Check parent chain for alignment to determine role
                let isUser = false;
                let parent = el.parentElement;
                
                for (let i = 0; i < 6 && parent; i++) {
                    const className = (typeof parent.className === 'string') ? parent.className : '';
                    
                    // User messages have justify-end or items-end in parent chain
                    if (className.includes('justify-end') || className.includes('items-end')) {
                        isUser = true;
                        break;
                    }
                    parent = parent.parentElement;
                }
                
                messages.push({
                    role: isUser ? 'user' : 'assistant',
                    content: text,
                    position: el.getBoundingClientRect().top
                });
            });
            
            // Deduplicate and sort
            const seen = new Set();
            const unique = messages.filter(m => {
                const key = m.content.substring(0, 100);
                if (seen.has(key)) return false;
                seen.add(key);
                return true;
            });
            
            unique.sort((a, b) => a.position - b.position);
            return unique.map(m => ({ role: m.role, content: m.content }));
        },
        
        perplexity: () => {
            const messages = [];
            const allMessages = [];
            
            const queries = document.querySelectorAll('[class*="query"], [class*="Question"], .ask-input');
            const answers = document.querySelectorAll('[class*="prose"], [class*="Answer"], .answer-text');
            
            queries.forEach(el => {
                const text = el.textContent.trim();
                if (text && text.length > 3) {
                    allMessages.push({
                        role: 'user',
                        content: text,
                        position: el.getBoundingClientRect().top
                    });
                }
            });
            
            answers.forEach(el => {
                const text = el.textContent.trim();
                if (text && text.length > 50) {
                    if (!el.closest('[class*="query"], [class*="Question"]')) {
                        allMessages.push({
                            role: 'assistant',
                            content: text,
                            position: el.getBoundingClientRect().top
                        });
                    }
                }
            });
            
            allMessages.sort((a, b) => a.position - b.position);
            
            return allMessages.map(m => ({ role: m.role, content: m.content }));
        },
        
        poe: () => {
            const messages = [];
            
            // Poe uses Message_row class with rightSide/leftSide to distinguish
            // User messages: rightSideMessageRow, rightSideMessageBubble
            // AI messages: leftSideMessageBubble, no rightSide
            document.querySelectorAll('[class*="Message_row"], [class*="ChatMessage_chatMessage"]').forEach(el => {
                // Safety check for className being a string
                const className = (typeof el.className === 'string') ? el.className : '';
                if (!className) return;
                
                const text = el.textContent.trim();
                if (!text || text.length < 3) return;
                
                // Skip if this is a container with nested messages
                if (el.querySelectorAll('[class*="Message_row"]').length > 0) return;
                
                // Check for user (right side) vs assistant (left side)
                const isUser = className.includes('rightSide');
                const isAssistant = className.includes('leftSide') || 
                                   (!className.includes('rightSide') && className.includes('Message_row'));
                
                if (isUser || isAssistant) {
                    messages.push({
                        role: isUser ? 'user' : 'assistant',
                        content: text,
                        position: el.getBoundingClientRect().top
                    });
                }
            });
            
            // Deduplicate and sort
            const seen = new Set();
            const unique = messages.filter(m => {
                const key = m.content.substring(0, 100);
                if (seen.has(key)) return false;
                seen.add(key);
                return true;
            });
            
            unique.sort((a, b) => a.position - b.position);
            return unique.map(m => ({ role: m.role, content: m.content }));
        }
    };

    // Send chat to server using GM_xmlhttpRequest (bypasses CSP)
    function sendToServer(platform, conversationId, userMessage, aiResponse) {
        log('Sending to server: ' + platform);
        
        GM_xmlhttpRequest({
            method: 'POST',
            url: SERVER_URL,
            headers: {
                'Content-Type': 'application/json'
            },
            data: JSON.stringify({
                platform: platform,
                conversation_id: conversationId,
                user_message: userMessage,
                ai_response: aiResponse,
                metadata: {
                    url: window.location.href,
                    timestamp: new Date().toISOString()
                }
            }),
            onload: function(response) {
                if (response.status === 200) {
                    captureCount++;
                    updateIndicatorText(captureCount);
                    log('Chat captured successfully', 'success');
                } else {
                    log('Server error: ' + response.status, 'error');
                }
            },
            onerror: function(error) {
                log('Connection error: ' + JSON.stringify(error), 'error');
            }
        });
    }

    // Process captured messages
    function processCapturedMessages(messages, platform) {
        if (messages.length < 2) return;

        let userMsg = null;
        let aiMsg = null;

        for (let i = messages.length - 1; i >= 0; i--) {
            if (messages[i].role === 'assistant' && !aiMsg) {
                aiMsg = messages[i].content;
            } else if (messages[i].role === 'user' && aiMsg && !userMsg) {
                userMsg = messages[i].content;
                break;
            }
        }

        if (userMsg && aiMsg) {
            const messageKey = userMsg.substring(0, 100) + aiMsg.substring(0, 100);
            
            if (messageKey !== lastCapturedMessage) {
                lastCapturedMessage = messageKey;
                const conversationId = window.location.pathname.split('/').pop() || 'unknown';
                sendToServer(platform, conversationId, userMsg, aiMsg);
            }
        }
    }

    // Main capture function
    function captureChats() {
        const platform = detectPlatform();
        
        if (platform === 'unknown') {
            return;
        }

        const captureFunction = captureFunctions[platform];
        if (!captureFunction) {
            return;
        }

        try {
            const messages = captureFunction();
            if (messages && messages.length > 0) {
                log('Found ' + messages.length + ' messages on ' + platform);
                processCapturedMessages(messages, platform);
            }
        } catch (error) {
            log('Capture error: ' + error.message, 'error');
        }
    }

    // Update indicator text - NO innerHTML, use textContent only
    function updateIndicatorText(count) {
        if (countElement) {
            countElement.textContent = count + ' captured';
        }
    }

    // Show notification - NO innerHTML
    function showNotification(message, type = 'info') {
        log(message, type);
        
        const notification = document.createElement('div');
        notification.className = 'chatcat-notification';
        notification.style.background = type === 'success' ? COLORS.accentGreen : type === 'error' ? COLORS.errorRed : COLORS.bgDarker;
        notification.style.color = type === 'success' ? COLORS.bgDark : COLORS.textPrimary;
        notification.style.border = '2px solid ' + (type === 'success' ? COLORS.accentGreen : type === 'error' ? COLORS.errorRed : COLORS.borderWhite);
        notification.textContent = message;  // Use textContent, not innerHTML
        
        document.body.appendChild(notification);
        
        setTimeout(() => {
            notification.style.transition = 'opacity 0.3s';
            notification.style.opacity = '0';
            setTimeout(() => notification.remove(), 300);
        }, 2000);
    }

    // Create indicator element - NO innerHTML, use DOM methods only
    function createIndicator() {
        // Remove any existing indicator
        const existing = document.getElementById('chatcat-indicator');
        if (existing) {
            log('Removing existing indicator');
            existing.remove();
        }
        
        // Create new indicator using DOM methods only (Trusted Types compatible)
        const el = document.createElement('div');
        el.id = 'chatcat-indicator';
        el.setAttribute('data-chatcat', 'true');
        
        // Create title element
        titleElement = document.createElement('div');
        titleElement.className = 'chatcat-title';
        titleElement.textContent = 'chatCAT';  // textContent, not innerHTML
        
        // Create count element
        countElement = document.createElement('div');
        countElement.className = 'chatcat-count';
        countElement.textContent = '0 captured';  // textContent, not innerHTML
        
        // Append children
        el.appendChild(titleElement);
        el.appendChild(countElement);
        
        // Apply inline styles as backup
        el.style.cssText = `
            position: fixed !important;
            bottom: 20px !important;
            right: 20px !important;
            width: 120px !important;
            height: 70px !important;
            background: ${COLORS.bgDarker} !important;
            color: ${COLORS.accentGreen} !important;
            border: 2px solid ${COLORS.borderWhite} !important;
            padding: 12px !important;
            font-family: 'Courier New', Consolas, Monaco, monospace !important;
            font-size: 11px !important;
            z-index: 2147483647 !important;
            cursor: pointer !important;
            box-shadow: 0 0 15px rgba(0, 255, 0, 0.3) !important;
            text-align: center !important;
            display: flex !important;
            flex-direction: column !important;
            justify-content: center !important;
            align-items: center !important;
            text-shadow: 0 0 10px rgba(0, 255, 0, 0.5) !important;
            user-select: none !important;
            pointer-events: auto !important;
            visibility: visible !important;
            opacity: 1 !important;
        `;
        
        // Load saved position
        try {
            const savedPosition = localStorage.getItem('chatcat-position');
            if (savedPosition) {
                const position = JSON.parse(savedPosition);
                el.style.left = position.left + 'px';
                el.style.top = position.top + 'px';
                el.style.right = 'auto';
                el.style.bottom = 'auto';
            }
        } catch (e) {
            log('Could not load saved position', 'warn');
        }
        
        // Setup drag and click handling
        setupDragAndClick(el);
        
        return el;
    }

    // Setup drag and click handlers
    function setupDragAndClick(el) {
        let isDragging = false;
        let dragStartTime = 0;
        let dragStartX = 0;
        let dragStartY = 0;
        let mouseMoved = false;
        const LONG_PRESS_DURATION = 500;
        const MOVE_THRESHOLD = 5;
        
        el.addEventListener('mousedown', (e) => {
            if (e.button !== 0) return;
            
            e.stopPropagation();
            e.preventDefault();
            
            dragStartTime = Date.now();
            dragStartX = e.clientX;
            dragStartY = e.clientY;
            mouseMoved = false;
            isDragging = false;
        });
        
        const handleMouseMove = (e) => {
            if (dragStartTime === 0) return;
            
            const deltaX = Math.abs(e.clientX - dragStartX);
            const deltaY = Math.abs(e.clientY - dragStartY);
            const timeSinceDown = Date.now() - dragStartTime;
            
            if (deltaX > MOVE_THRESHOLD || deltaY > MOVE_THRESHOLD) {
                mouseMoved = true;
            }
            
            if ((timeSinceDown > LONG_PRESS_DURATION || mouseMoved) && !isDragging) {
                isDragging = true;
                el.classList.add('chatcat-dragging');
                el.style.cursor = 'move';
            }
            
            if (isDragging) {
                e.preventDefault();
                e.stopPropagation();
                
                const rect = el.getBoundingClientRect();
                let newLeft = rect.left + (e.clientX - dragStartX);
                let newTop = rect.top + (e.clientY - dragStartY);
                
                const maxX = window.innerWidth - el.offsetWidth;
                const maxY = window.innerHeight - el.offsetHeight;
                newLeft = Math.max(0, Math.min(newLeft, maxX));
                newTop = Math.max(0, Math.min(newTop, maxY));
                
                el.style.left = newLeft + 'px';
                el.style.top = newTop + 'px';
                el.style.right = 'auto';
                el.style.bottom = 'auto';
                
                dragStartX = e.clientX;
                dragStartY = e.clientY;
            }
        };
        
        const handleMouseUp = (e) => {
            if (dragStartTime === 0) return;
            
            e.stopPropagation();
            
            const wasDragging = isDragging;
            
            if (wasDragging) {
                const rect = el.getBoundingClientRect();
                try {
                    localStorage.setItem('chatcat-position', JSON.stringify({
                        left: rect.left,
                        top: rect.top
                    }));
                } catch (e) {}
                
                el.classList.remove('chatcat-dragging');
                el.style.cursor = 'pointer';
                showNotification('Position Saved', 'success');
            } else if (!mouseMoved) {
                e.preventDefault();
                
                const dashboardUrl = 'http://localhost:8765/';
                
                try {
                    GM_openInTab(dashboardUrl, { active: true, insert: true, setParent: false });
                } catch (err) {
                    window.open(dashboardUrl, 'chatcat_dashboard');
                }
            }
            
            isDragging = false;
            dragStartTime = 0;
            mouseMoved = false;
        };
        
        document.addEventListener('mousemove', handleMouseMove);
        document.addEventListener('mouseup', handleMouseUp);
        
        document.addEventListener('mouseleave', () => {
            if (isDragging) {
                el.classList.remove('chatcat-dragging');
                el.style.cursor = 'pointer';
            }
            isDragging = false;
            dragStartTime = 0;
            mouseMoved = false;
        });
        
        // Hover effects
        el.addEventListener('mouseenter', () => {
            if (!isDragging) {
                el.style.background = COLORS.accentGreen;
                el.style.color = COLORS.bgDark;
                el.style.boxShadow = '0 0 25px rgba(0, 255, 0, 0.8)';
                el.style.textShadow = 'none';
            }
        });
        
        el.addEventListener('mouseleave', () => {
            if (!isDragging) {
                el.style.background = COLORS.bgDarker;
                el.style.color = COLORS.accentGreen;
                el.style.boxShadow = '0 0 15px rgba(0, 255, 0, 0.3)';
                el.style.textShadow = '0 0 10px rgba(0, 255, 0, 0.5)';
            }
        });
    }

    // Append indicator to DOM
    function appendIndicator() {
        if (!indicator) {
            indicator = createIndicator();
        }
        
        const targets = [
            document.body,
            document.documentElement
        ];
        
        for (const target of targets) {
            if (target) {
                try {
                    target.appendChild(indicator);
                    log('Indicator appended to ' + (target.id || target.tagName));
                    return true;
                } catch (e) {
                    log('Failed to append to ' + (target.id || target.tagName) + ': ' + e.message, 'warn');
                }
            }
        }
        
        log('Could not find valid append target', 'error');
        return false;
    }

    // Ensure indicator is visible
    function ensureIndicatorVisible() {
        const existingIndicator = document.getElementById('chatcat-indicator');
        
        if (!existingIndicator || !document.body.contains(existingIndicator)) {
            log('Indicator missing, recreating...');
            indicator = createIndicator();
            appendIndicator();
            updateIndicatorText(captureCount);
        }
    }

    // Initialise
    function init() {
        const platform = detectPlatform();
        log('Initialising on platform: ' + platform);
        log('Document ready state: ' + document.readyState);
        
        // Inject styles first
        injectStyles();
        
        // Create and append indicator
        indicator = createIndicator();
        
        if (document.body) {
            appendIndicator();
            log('Indicator created successfully', 'success');
        } else {
            log('Body not ready, waiting...', 'warn');
            initAttempts++;
            
            if (initAttempts < MAX_INIT_ATTEMPTS) {
                setTimeout(init, 500);
                return;
            }
        }
        
        // Periodically ensure indicator is visible
        setInterval(ensureIndicatorVisible, INDICATOR_CHECK_INTERVAL);
        
        // Start periodic capture
        setInterval(captureChats, CHECK_INTERVAL);
        
        // Initial capture
        setTimeout(captureChats, 2000);
        
        log('Initialised successfully', 'success');
    }

    // Handle SPA navigation
    let lastUrl = location.href;
    const urlObserver = new MutationObserver(() => {
        const url = location.href;
        if (url !== lastUrl) {
            lastUrl = url;
            log('URL changed, ensuring indicator visible');
            setTimeout(ensureIndicatorVisible, 500);
        }
    });

    // Start when ready
    function startWhenReady() {
        if (document.readyState === 'complete' || document.readyState === 'interactive') {
            setTimeout(init, 100);
        } else {
            document.addEventListener('DOMContentLoaded', () => setTimeout(init, 100));
        }
        
        window.addEventListener('load', () => {
            setTimeout(ensureIndicatorVisible, 1000);
        });
        
        urlObserver.observe(document, { subtree: true, childList: true });
    }

    startWhenReady();

})();
