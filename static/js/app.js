// ===== MODERN AGENTIC AI APPLICATION =====
class AgenticAI {
    constructor() {
        // Core properties
        this.socket = null;
        this.isConnected = false;
        this.clientId = null;

        // UI state
        this.isTyping = false;
        this.messageHistory = [];
        this.isInitialized = false;
        this.initializationErrors = [];

        // Performance tracking
        this.performance = {
            connectionStart: null,
            lastMessageTime: null,
            totalMessages: 0
        };

        // DOM elements cache
        this.elements = this.initializeElements();

        // Initialize app
        this.init();
    }

    initializeElements() {
        return {
            // Core UI
            app: document.getElementById('app'),
            loadingScreen: document.getElementById('loading-screen'),

            // Header
            connectionBadge: document.getElementById('connection-badge'),
            connectionText: document.querySelector('.connection-text'),
            connectionDot: document.querySelector('.connection-dot'),

            // Action buttons
            clearBtn: document.getElementById('clear-btn'),

            // Main chat
            messagesArea: document.getElementById('messages-area'),
            welcomeScreen: document.getElementById('welcome-screen'),
            messagesContainer: document.getElementById('messages-container'),

            // Input area
            messageInput: document.getElementById('message-input'),
            sendBtn: document.getElementById('send-btn'),
            sendIcon: document.querySelector('.send-icon'),
            loadingIcon: document.querySelector('.loading-icon'),
            charCount: document.getElementById('char-count'),

            // Indicators
            typingIndicator: document.getElementById('typing-indicator'),
            statusIndicator: document.getElementById('status-indicator'),
            statusText: document.getElementById('status-text'),

            // Templates
            userMessageTemplate: document.getElementById('user-message-template'),
            aiMessageTemplate: document.getElementById('ai-message-template'),
            errorMessageTemplate: document.getElementById('error-message-template'),
            sourceLinkTemplate: document.getElementById('source-link-template'),

            // Toast container
            toastContainer: document.getElementById('toast-container')
        };
    }

    // ===== INITIALIZATION =====
    init() {
        console.log('🚀 Initializing Agentic AI...');
        try {
            this.setupEventListeners();
            this.setupQuickStarters();

            // Connect socket with timeout fallback
            this.connectSocket();

            // Fallback to hide loading screen after 3 seconds regardless
            setTimeout(() => {
                if (!this.isInitialized) {
                    console.warn('⚠️ Initialization timeout, forcing completion');
                    this.completeInitialization();
                }
            }, 3000);

            console.log('✅ Agentic AI basic initialization completed');
        } catch (error) {
            console.error('❌ Initialization error:', error);
            this.initializationErrors.push(error);
            this.completeInitialization();
        }
    }

    completeInitialization() {
        if (this.isInitialized) return;

        this.isInitialized = true;
        this.hideLoadingScreen();

        // Focus input after a delay
        setTimeout(() => {
            try {
                if (this.elements.messageInput) {
                    this.elements.messageInput.focus();
                }
            } catch (error) {
                console.debug('Focus error (ignored):', error);
            }
        }, 300);

        if (this.initializationErrors.length > 0) {
            console.warn('Initialization completed with warnings:', this.initializationErrors);
        } else {
            console.log('✅ Initialization completed successfully');
        }
    }

    setupEventListeners() {
        try {
            // Message input
            if (this.elements.messageInput) {
                this.elements.messageInput.addEventListener('input', () => this.handleInputChange());
                this.elements.messageInput.addEventListener('keydown', (e) => this.handleInputKeydown(e));
                this.elements.messageInput.addEventListener('paste', () => {
                    setTimeout(() => this.handleInputChange(), 0);
                });
            }

            // Send button
            if (this.elements.sendBtn) {
                this.elements.sendBtn.addEventListener('click', () => this.sendMessage());
            }

            // Clear button
            if (this.elements.clearBtn) {
                this.elements.clearBtn.addEventListener('click', () => this.clearConversation());
            }

            // Window events
            window.addEventListener('beforeunload', () => this.handleBeforeUnload());
            window.addEventListener('focus', () => this.handleWindowFocus());
            document.addEventListener('visibilitychange', () => this.handleVisibilityChange());

            // Global keyboard shortcuts
            document.addEventListener('keydown', (e) => this.handleGlobalKeydown(e));
        } catch (error) {
            console.warn('Event listeners setup error:', error);
            this.initializationErrors.push(error);
        }
    }

    setupQuickStarters() {
        try {
            const starterBtns = document.querySelectorAll('.starter-btn');
            starterBtns.forEach(btn => {
                btn.addEventListener('click', () => {
                    const query = btn.dataset.query;
                    if (query && this.elements.messageInput) {
                        this.elements.messageInput.value = query;
                        this.handleInputChange();
                        this.elements.messageInput.focus();
                    }
                });
            });
        } catch (error) {
            console.warn('Quick starters setup error:', error);
            this.initializationErrors.push(error);
        }
    }

    // ===== SOCKET CONNECTION =====
    connectSocket() {
        if (typeof io === 'undefined') {
            console.warn('❌ Socket.IO not loaded - running in offline mode');
            this.updateConnectionStatus('disconnected');
            this.completeInitialization();
            return;
        }

        this.performance.connectionStart = performance.now();
        this.updateConnectionStatus('connecting');

        try {
            this.socket = io({
                transports: ['websocket', 'polling'],
                timeout: 10000,
                reconnection: true,
                reconnectionAttempts: 3,
                reconnectionDelay: 1000,
                reconnectionDelayMax: 3000
            });

            this.setupSocketEvents();
        } catch (error) {
            console.error('Socket connection failed:', error);
            this.updateConnectionStatus('disconnected');
            this.completeInitialization();
        }
    }

    setupSocketEvents() {
        // Connection success
        this.socket.on('connect', () => {
            const connectionTime = performance.now() - this.performance.connectionStart;
            console.log(`⚡ Connected in ${connectionTime.toFixed(2)}ms`);
            this.isConnected = true;
            this.updateConnectionStatus('connected');
        });

        // Disconnection
        this.socket.on('disconnect', (reason) => {
            console.log('🔌 Disconnected:', reason);
            this.isConnected = false;
            this.updateConnectionStatus('disconnected');
            this.hideTypingIndicator();
            this.hideStatusIndicator();
        });

        // Server connection confirmed
        this.socket.on('connected', (data) => {
            console.log('✅ Server connection established:', data);
            this.clientId = data.client_id;
            
            if (!this.messageHistory.length) {
                this.showToast('Connected to Agentic AI', 'success', 3000);
            }
            
            this.completeInitialization();
        });

        // Message events
        this.socket.on('status_update', (data) => {
            this.showStatusIndicator(data.message);
        });

        this.socket.on('final_response', (data) => {
            this.handleFinalResponse(data);
        });

        this.socket.on('error', (data) => {
            this.handleSocketError(data);
        });

        this.socket.on('history_cleared', (data) => {
            this.clearMessages();
            this.showWelcomeScreen();
            this.showToast(data.message || 'Conversation cleared', 'success', 2000);
        });

        // Connection error handling
        this.socket.on('connect_error', (error) => {
            console.warn('Connection error:', error);
            this.updateConnectionStatus('disconnected');
            setTimeout(() => this.completeInitialization(), 1000);
        });

        this.socket.on('reconnect', (attemptNumber) => {
            console.log(`🔄 Reconnected after ${attemptNumber} attempts`);
            this.showToast('Reconnected successfully!', 'success', 2000);
        });

        this.socket.on('reconnect_failed', () => {
            console.warn('❌ Failed to reconnect');
            this.showToast('Connection lost. Working in offline mode.', 'warning', 3000);
        });
    }

    // ===== UI UPDATES =====
    hideLoadingScreen() {
        if (this.elements.loadingScreen) {
            this.elements.loadingScreen.style.opacity = '0';
            this.elements.loadingScreen.style.pointerEvents = 'none';
            setTimeout(() => {
                this.elements.loadingScreen.style.display = 'none';
            }, 300);
        }
    }

    updateConnectionStatus(status) {
        if (!this.elements.connectionBadge) return;

        // Remove all status classes
        this.elements.connectionBadge.className = 'connection-badge';
        // Add new status class
        this.elements.connectionBadge.classList.add(status);

        // Update text
        const statusText = {
            connecting: 'Connecting...',
            connected: 'Connected',
            disconnected: 'Offline'
        };

        if (this.elements.connectionText) {
            this.elements.connectionText.textContent = statusText[status] || 'Unknown';
        }
    }

    // ===== MESSAGE HANDLING =====
    sendMessage() {
        const message = this.elements.messageInput?.value.trim();
        if (!message) {
            return;
        }

        if (!this.isConnected) {
            this.showToast('Not connected to server. Please check your connection.', 'warning', 3000);
            return;
        }

        // Track performance
        this.performance.lastMessageTime = performance.now();
        this.performance.totalMessages++;

        // Hide welcome screen
        this.hideWelcomeScreen();

        // Add user message
        this.addUserMessage(message);

        // Clear input and update UI
        this.elements.messageInput.value = '';
        this.handleInputChange();
        this.showTypingIndicator();
        this.setInputEnabled(false);

        // Send to server
        try {
            this.socket.emit('send_message', { message });
            
            // Store in history
            this.messageHistory.push({
                type: 'user',
                message,
                timestamp: Date.now()
            });
        } catch (error) {
            console.error('Error sending message:', error);
            this.handleSocketError({ message: 'Failed to send message. Please try again.' });
        }

        // Auto-resize input
        this.elements.messageInput.style.height = 'auto';
    }

    handleInputChange() {
        if (!this.elements.messageInput) return;

        const value = this.elements.messageInput.value;
        const length = value.length;
        const maxLength = 4000;

        // Update character count
        if (this.elements.charCount) {
            this.elements.charCount.textContent = length;

            // Add warning class if approaching limit
            if (length > maxLength * 0.8) {
                this.elements.charCount.style.color = 'var(--color-warning-500)';
            } else {
                this.elements.charCount.style.color = 'var(--text-muted)';
            }
        }

        // Update send button
        this.updateSendButton();

        // Auto-resize textarea
        try {
            this.elements.messageInput.style.height = 'auto';
            this.elements.messageInput.style.height = Math.min(this.elements.messageInput.scrollHeight, 128) + 'px';
        } catch (error) {
            // Ignore resize errors
        }
    }

    handleInputKeydown(event) {
        if (event.key === 'Enter' && !event.shiftKey) {
            event.preventDefault();
            this.sendMessage();
        } else if (event.key === 'Escape') {
            try {
                this.elements.messageInput.blur();
            } catch (error) {
                // Ignore blur errors
            }
        }
    }

    updateSendButton() {
        if (!this.elements.sendBtn || !this.elements.messageInput) return;

        const hasMessage = this.elements.messageInput.value.trim().length > 0;
        const canSend = hasMessage && this.isConnected && !this.isTyping;

        this.elements.sendBtn.disabled = !canSend;

        if (canSend) {
            this.elements.sendBtn.classList.add('ready');
        } else {
            this.elements.sendBtn.classList.remove('ready');
        }
    }

    setInputEnabled(enabled) {
        if (this.elements.messageInput) {
            this.elements.messageInput.disabled = !enabled;
        }
        
        this.updateSendButton();
        
        if (enabled) {
            try {
                this.elements.messageInput?.focus();
            } catch (error) {
                // Ignore focus errors
            }
        }
    }

    // ===== MESSAGE DISPLAY =====
    addUserMessage(message) {
        if (!this.elements.userMessageTemplate || !this.elements.messagesContainer) return;

        const messageElement = this.elements.userMessageTemplate.content.cloneNode(true);
        const textElement = messageElement.querySelector('.message-text');
        const timeElement = messageElement.querySelector('.message-time');

        if (textElement) textElement.textContent = message;
        if (timeElement) timeElement.textContent = new Date().toLocaleTimeString();

        this.elements.messagesContainer.appendChild(messageElement);
        this.scrollToBottom();
    }

    handleFinalResponse(data) {
        this.hideTypingIndicator();
        this.hideStatusIndicator();
        this.setInputEnabled(true);
        this.isTyping = false;

        if (!this.elements.aiMessageTemplate || !this.elements.messagesContainer) return;

        const messageElement = this.elements.aiMessageTemplate.content.cloneNode(true);
        const textElement = messageElement.querySelector('.message-text');
        const timeElement = messageElement.querySelector('.message-time');
        const confidenceElement = messageElement.querySelector('.confidence-badge');
        const processingElement = messageElement.querySelector('.processing-time');
        const methodElement = messageElement.querySelector('.method-badge');
        const sourcesContainer = messageElement.querySelector('.message-sources');

        // Set response text
        if (textElement && data.response) {
            textElement.innerHTML = this.formatMarkdown(data.response);
        }

        // Set timestamp
        if (timeElement) {
            timeElement.textContent = new Date().toLocaleTimeString();
        }

        // Set confidence
        if (confidenceElement && data.confidence) {
            confidenceElement.style.display = 'inline-flex';
            const confidenceValue = confidenceElement.querySelector('.confidence-value');
            if (confidenceValue) confidenceValue.textContent = `${data.confidence}%`;
        }

        // Set processing time
        if (processingElement && data.processing_time) {
            processingElement.style.display = 'inline-flex';
            const timeValue = processingElement.querySelector('.time-value');
            if (timeValue) timeValue.textContent = `${data.processing_time}s`;
        }

        // Set method
        if (methodElement && data.method) {
            methodElement.style.display = 'inline-flex';
            const methodValue = methodElement.querySelector('.method-value');
            if (methodValue) methodValue.textContent = data.method;
        }

        // Add sources
        if (sourcesContainer && data.sources && data.sources.length > 0) {
            sourcesContainer.style.display = 'block';
            const sourcesList = sourcesContainer.querySelector('.sources-list');
            if (sourcesList) {
                sourcesList.innerHTML = '';
                data.sources.forEach(source => {
                    const sourceElement = this.createSourceLink(source);
                    if (sourceElement) sourcesList.appendChild(sourceElement);
                });
            }
        }

        this.elements.messagesContainer.appendChild(messageElement);
        this.scrollToBottom();
    }

    createSourceLink(source) {
        if (!this.elements.sourceLinkTemplate) return null;

        const linkElement = this.elements.sourceLinkTemplate.content.cloneNode(true);
        const link = linkElement.querySelector('.source-link');
        const title = linkElement.querySelector('.source-title');
        const domain = linkElement.querySelector('.source-domain');

        if (link && source.url) {
            link.href = source.url;
        }

        if (title && source.name) {
            title.textContent = source.name;
        }

        if (domain && source.url) {
            try {
                const url = new URL(source.url);
                domain.textContent = url.hostname;
            } catch (error) {
                domain.textContent = '';
            }
        }

        return linkElement;
    }

    // ===== INDICATORS =====
    showTypingIndicator() {
        this.isTyping = true;
        this.updateSendButton();
        if (this.elements.typingIndicator) {
            this.elements.typingIndicator.style.display = 'flex';
        }
        this.scrollToBottom();
    }

    hideTypingIndicator() {
        this.isTyping = false;
        this.updateSendButton();
        if (this.elements.typingIndicator) {
            this.elements.typingIndicator.style.display = 'none';
        }
    }

    showStatusIndicator(message) {
        if (this.elements.statusIndicator) {
            this.elements.statusIndicator.style.display = 'flex';
        }
        if (this.elements.statusText) {
            this.elements.statusText.textContent = message;
        }
        this.scrollToBottom();
    }

    hideStatusIndicator() {
        if (this.elements.statusIndicator) {
            this.elements.statusIndicator.style.display = 'none';
        }
    }

    // ===== SCREEN MANAGEMENT =====
    hideWelcomeScreen() {
        if (this.elements.welcomeScreen) {
            this.elements.welcomeScreen.style.display = 'none';
        }
        if (this.elements.messagesContainer) {
            this.elements.messagesContainer.style.display = 'block';
        }
    }

    showWelcomeScreen() {
        if (this.elements.welcomeScreen) {
            this.elements.welcomeScreen.style.display = 'flex';
        }
        if (this.elements.messagesContainer) {
            this.elements.messagesContainer.style.display = 'none';
        }
    }

    // ===== ACTIONS =====
    clearConversation() {
        if (this.socket && this.isConnected) {
            this.socket.emit('clear_history');
        } else {
            this.clearMessages();
            this.showWelcomeScreen();
            this.showToast('Conversation cleared locally', 'success', 2000);
        }
    }

    clearMessages() {
        if (this.elements.messagesContainer) {
            this.elements.messagesContainer.innerHTML = '';
        }
        this.messageHistory = [];
    }

    // ===== ERROR HANDLING =====
    handleSocketError(data) {
        this.hideTypingIndicator();
        this.hideStatusIndicator();
        this.setInputEnabled(true);
        this.showToast(data?.message || 'An error occurred', 'error', 3000);

        // Add error message to chat
        if (this.elements.errorMessageTemplate && this.elements.messagesContainer) {
            const messageElement = this.elements.errorMessageTemplate.content.cloneNode(true);
            const textElement = messageElement.querySelector('.message-text');
            const timeElement = messageElement.querySelector('.message-time');

            if (textElement) {
                textElement.textContent = data?.message || 'An error occurred while processing your request.';
            }
            if (timeElement) {
                timeElement.textContent = new Date().toLocaleTimeString();
            }

            this.elements.messagesContainer.appendChild(messageElement);
            this.scrollToBottom();
        }
    }

    // ===== UTILITIES =====
    showToast(message, type = 'info', duration = 4000) {
        if (!this.isInitialized) {
            console.log(`Toast (suppressed during init): ${message} (${type})`);
            return;
        }

        if (!this.elements.toastContainer) {
            console.log(`Toast: ${message} (${type})`);
            return;
        }

        try {
            const toast = document.createElement('div');
            toast.className = `toast ${type}`;

            const icon = this.getToastIcon(type);
            const closeBtn = document.createElement('button');
            closeBtn.className = 'toast-close';
            closeBtn.innerHTML = '✕';

            toast.innerHTML = `
                <div class="toast-icon">${icon}</div>
                <div class="toast-content">${message}</div>
                ${closeBtn.outerHTML}
            `;

            this.elements.toastContainer.appendChild(toast);

            // Auto remove
            setTimeout(() => {
                if (toast.parentElement) {
                    toast.remove();
                }
            }, duration);

            // Manual close
            const closeButton = toast.querySelector('.toast-close');
            if (closeButton) {
                closeButton.addEventListener('click', () => {
                    toast.remove();
                });
            }
        } catch (error) {
            console.error('Toast error:', error);
        }
    }

    getToastIcon(type) {
        const icons = {
            success: '✓',
            error: '✕',
            warning: '⚠️',
            info: 'ℹ️'
        };
        return icons[type] || icons.info;
    }

    formatMarkdown(text) {
        // Basic markdown formatting
        return text
            .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
            .replace(/\*(.*?)\*/g, '<em>$1</em>')
            .replace(/`(.*?)`/g, '<code>$1</code>')
            .replace(/\n/g, '<br>');
    }

    scrollToBottom() {
        setTimeout(() => {
            if (this.elements.messagesArea) {
                this.elements.messagesArea.scrollTop = this.elements.messagesArea.scrollHeight;
            }
        }, 100);
    }

    // ===== EVENT HANDLERS =====
    handleBeforeUnload() {
        if (this.socket && this.isConnected) {
            this.socket.disconnect();
        }
    }

    handleWindowFocus() {
        if (this.elements.messageInput && this.isInitialized) {
            try {
                this.elements.messageInput.focus();
            } catch (error) {
                // Ignore focus errors
            }
        }
    }

    handleVisibilityChange() {
        if (!document.hidden && this.elements.messageInput && this.isInitialized) {
            try {
                this.elements.messageInput.focus();
            } catch (error) {
                // Ignore focus errors
            }
        }
    }

    handleGlobalKeydown(event) {
        // Ctrl/Cmd + K to focus input
        if ((event.ctrlKey || event.metaKey) && event.key === 'k') {
            event.preventDefault();
            if (this.elements.messageInput) {
                try {
                    this.elements.messageInput.focus();
                } catch (error) {
                    // Ignore focus errors
                }
            }
        }
    }
}
