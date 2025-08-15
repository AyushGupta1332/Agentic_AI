// ===== AGENTIC AI FRONTEND APPLICATION =====
class AgenticAI {
    constructor() {
        this.socket = null;
        this.isConnected = false;
        this.clientId = null;
        this.isDebugMode = false;
        this.currentTypingTimeout = null;
        
        // DOM Elements
        this.elements = {
            messagesContainer: document.getElementById('messages-container'),
            messageInput: document.getElementById('message-input'),
            sendBtn: document.getElementById('send-btn'),
            clearBtn: document.getElementById('clear-btn'),
            toggleDebugBtn: document.getElementById('toggle-debug'),
            connectionStatus: document.getElementById('connection-status'),
            statusIndicator: document.querySelector('.status-indicator'),
            statusText: document.querySelector('.status-text'),
            typingIndicator: document.getElementById('typing-indicator'),
            statusUpdates: document.getElementById('status-updates'),
            statusMessage: document.getElementById('status-message'),
            debugPanel: document.getElementById('debug-panel'),
            debugContent: document.getElementById('debug-content'),
            closeDebugBtn: document.getElementById('close-debug'),
            charCount: document.getElementById('char-count'),
            loadingOverlay: document.getElementById('loading-overlay')
        };
        
        // Templates
        this.templates = {
            userMessage: document.getElementById('user-message-template'),
            aiMessage: document.getElementById('ai-message-template'),
            errorMessage: document.getElementById('error-message-template')
        };
        
        this.init();
    }
    
    // ===== INITIALIZATION =====
    init() {
        console.log('🚀 Initializing Agentic AI...');
        this.showLoadingOverlay();
        this.setupEventListeners();
        this.connectSocket();
        this.setupAutoResize();
    }
    
    setupEventListeners() {
        // Send message events
        this.elements.sendBtn.addEventListener('click', () => this.sendMessage());
        this.elements.messageInput.addEventListener('keydown', (e) => this.handleKeydown(e));
        this.elements.messageInput.addEventListener('input', () => this.handleInputChange());
        
        // Control buttons
        this.elements.clearBtn.addEventListener('click', () => this.clearConversation());
        this.elements.toggleDebugBtn.addEventListener('click', () => this.toggleDebugPanel());
        this.elements.closeDebugBtn.addEventListener('click', () => this.toggleDebugPanel());
        
        // Auto-focus input when page loads
        window.addEventListener('load', () => {
            this.elements.messageInput.focus();
            this.hideLoadingOverlay();
        });
        
        // Handle window resize for responsive design
        window.addEventListener('resize', () => this.handleResize());
    }
    
    setupAutoResize() {
        const input = this.elements.messageInput;
        input.addEventListener('input', () => {
            input.style.height = 'auto';
            input.style.height = Math.min(input.scrollHeight, 120) + 'px';
        });
    }
    
    // ===== SOCKET CONNECTION =====
    connectSocket() {
        try {
            this.socket = io({
                transports: ['websocket', 'polling']
            });
            
            this.socket.on('connect', () => this.handleConnect());
            this.socket.on('disconnect', () => this.handleDisconnect());
            this.socket.on('connected', (data) => this.handleConnected(data));
            this.socket.on('status_update', (data) => this.handleStatusUpdate(data));
            this.socket.on('final_response', (data) => this.handleFinalResponse(data));
            this.socket.on('debug_info', (data) => this.handleDebugInfo(data));
            this.socket.on('error', (data) => this.handleError(data));
            this.socket.on('history_cleared', (data) => this.handleHistoryCleared(data));
            
        } catch (error) {
            console.error('Failed to connect to socket:', error);
            this.showError('Failed to connect to server. Please refresh the page.');
        }
    }
    
    handleConnect() {
        console.log('🔌 Connected to server');
        this.isConnected = true;
        this.updateConnectionStatus('connected', 'Connected');
    }
    
    handleDisconnect() {
        console.log('🔌 Disconnected from server');
        this.isConnected = false;
        this.updateConnectionStatus('disconnected', 'Disconnected');
        this.hideTypingIndicator();
        this.hideStatusUpdates();
    }
    
    handleConnected(data) {
        console.log('✅ Connection established:', data);
        this.clientId = data.client_id;
        this.showNotification(data.message || 'Connected to Agentic AI', 'success');
        this.hideLoadingOverlay();
    }
    
    // ===== MESSAGE HANDLING =====
    sendMessage() {
        const message = this.elements.messageInput.value.trim();
        if (!message || !this.isConnected) return;
        
        // Add user message to UI immediately
        this.addUserMessage(message);
        
        // Send to server
        this.socket.emit('send_message', { message: message });
        
        // Clear input and show typing indicator
        this.elements.messageInput.value = '';
        this.elements.messageInput.style.height = 'auto';
        this.updateCharCount();
        this.updateSendButton();
        this.showTypingIndicator();
        
        // Disable input temporarily
        this.setInputEnabled(false);
    }
    
    handleKeydown(event) {
        if (event.key === 'Enter' && !event.shiftKey) {
            event.preventDefault();
            this.sendMessage();
        }
    }
    
    handleInputChange() {
        this.updateCharCount();
        this.updateSendButton();
    }
    
    // ===== UI UPDATES =====
    addUserMessage(message) {
        const messageElement = this.createMessageElement(this.templates.userMessage, {
            text: message,
            time: this.getCurrentTime()
        });
        this.appendMessage(messageElement);
    }
    
    addAIMessage(data) {
        const messageElement = this.createMessageElement(this.templates.aiMessage, {
            text: data.response,
            time: this.getCurrentTime(),
            confidence: data.confidence,
            processingTime: data.processing_time,
            method: data.method,
            sources: data.sources
        });
        this.appendMessage(messageElement);
    }
    
    addErrorMessage(message) {
        const messageElement = this.createMessageElement(this.templates.errorMessage, {
            text: message,
            time: this.getCurrentTime()
        });
        this.appendMessage(messageElement);
    }
    
    createMessageElement(template, data) {
        const messageElement = template.content.cloneNode(true);
        const textElement = messageElement.querySelector('.message-text');
        const timeElement = messageElement.querySelector('.message-time');
        
        // Set message text (render as markdown for AI messages)
        if (template === this.templates.aiMessage) {
            textElement.innerHTML = marked.parse(data.text);
            this.highlightCode(textElement);
        } else {
            textElement.textContent = data.text;
        }
        
        // Set timestamp
        timeElement.textContent = data.time;
        
        // Add AI-specific metadata
        if (data.confidence !== undefined) {
            const confidenceElement = messageElement.querySelector('.confidence-score');
            confidenceElement.textContent = `${data.confidence}%`;
            confidenceElement.style.display = 'inline-flex';
        }
        
        if (data.processingTime !== undefined) {
            const processingElement = messageElement.querySelector('.processing-time');
            processingElement.textContent = `${data.processingTime}s`;
            processingElement.style.display = 'inline';
        }
        
        if (data.method) {
            const methodElement = messageElement.querySelector('.method-used');
            methodElement.textContent = data.method;
            methodElement.style.display = 'inline';
        }
        
        // Add sources
        if (data.sources && data.sources.length > 0) {
            const sourcesElement = messageElement.querySelector('.message-sources');
            sourcesElement.innerHTML = '<h4>Sources:</h4>' + 
                data.sources.map(source => 
                    `<a href="${source.url}" target="_blank" rel="noopener noreferrer" class="source-link">
                        📄 ${source.name || 'Source'}
                    </a>`
                ).join('');
            sourcesElement.style.display = 'block';
        }
        
        return messageElement;
    }
    
    appendMessage(messageElement) {
        this.elements.messagesContainer.appendChild(messageElement);
        this.scrollToBottom();
    }
    
    // ===== STATUS HANDLING =====
    handleStatusUpdate(data) {
        console.log('📊 Status update:', data.message);
        this.showStatusUpdate(data.message);
    }
    
    handleFinalResponse(data) {
        console.log('✅ Received final response:', data);
        this.hideTypingIndicator();
        this.hideStatusUpdates();
        this.addAIMessage(data);
        this.setInputEnabled(true);
        this.elements.messageInput.focus();
    }
    
    handleDebugInfo(data) {
        console.log('🐛 Debug info:', data);
        if (this.isDebugMode) {
            this.addDebugInfo(data.title, data.content);
        }
    }
    
    handleError(data) {
        console.error('❌ Error:', data.message);
        this.hideTypingIndicator();
        this.hideStatusUpdates();
        this.addErrorMessage(data.message);
        this.setInputEnabled(true);
        this.showNotification('Error: ' + data.message, 'error');
    }
    
    handleHistoryCleared(data) {
        console.log('🗑️ History cleared:', data.message);
        this.clearMessages();
        this.showNotification(data.message, 'success');
    }
    
    // ===== UI HELPER METHODS =====
    showTypingIndicator() {
        this.elements.typingIndicator.style.display = 'flex';
        this.scrollToBottom();
    }
    
    hideTypingIndicator() {
        this.elements.typingIndicator.style.display = 'none';
    }
    
    showStatusUpdates() {
        this.elements.statusUpdates.style.display = 'block';
    }
    
    hideStatusUpdates() {
        this.elements.statusUpdates.style.display = 'none';
    }
    
    showStatusUpdate(message) {
        this.elements.statusMessage.textContent = message;
        this.showStatusUpdates();
    }
    
    updateConnectionStatus(status, text) {
        this.elements.statusIndicator.className = `fas fa-circle status-indicator ${status}`;
        this.elements.statusText.textContent = text;
    }
    
    setInputEnabled(enabled) {
        this.elements.messageInput.disabled = !enabled;
        this.elements.sendBtn.disabled = !enabled || !this.elements.messageInput.value.trim();
        
        if (enabled) {
            this.elements.messageInput.focus();
        }
    }
    
    updateSendButton() {
        const hasText = this.elements.messageInput.value.trim().length > 0;
        this.elements.sendBtn.disabled = !hasText || !this.isConnected;
    }
    
    updateCharCount() {
        const count = this.elements.messageInput.value.length;
        this.elements.charCount.textContent = `${count}/2000`;
        
        if (count > 1800) {
            this.elements.charCount.style.color = 'var(--error-color)';
        } else if (count > 1500) {
            this.elements.charCount.style.color = 'var(--warning-color)';
        } else {
            this.elements.charCount.style.color = 'var(--text-muted)';
        }
    }
    
    scrollToBottom() {
        requestAnimationFrame(() => {
            this.elements.messagesContainer.scrollTop = this.elements.messagesContainer.scrollHeight;
        });
    }
    
    // ===== ACTIONS =====
    clearConversation() {
        if (confirm('Are you sure you want to clear the conversation history?')) {
            this.socket.emit('clear_history');
        }
    }
    
    clearMessages() {
        // Keep the welcome message, remove everything else
        const messages = this.elements.messagesContainer.querySelectorAll('.message:not(.welcome-message)');
        messages.forEach(message => message.remove());
    }
    
    toggleDebugPanel() {
        this.isDebugMode = !this.isDebugMode;
        this.elements.debugPanel.classList.toggle('active');
        
        if (this.isDebugMode) {
            this.elements.toggleDebugBtn.innerHTML = '<i class="fas fa-bug"></i> Hide Debug';
        } else {
            this.elements.toggleDebugBtn.innerHTML = '<i class="fas fa-bug"></i> Debug';
        }
    }
    
    addDebugInfo(title, content) {
        const debugEntry = document.createElement('div');
        debugEntry.className = 'debug-entry';
        debugEntry.innerHTML = `
            <h4>${title}</h4>
            <pre><code>${JSON.stringify(content, null, 2)}</code></pre>
            <hr>
        `;
        this.elements.debugContent.appendChild(debugEntry);
        this.elements.debugContent.scrollTop = this.elements.debugContent.scrollHeight;
    }
    
    // ===== UTILITY METHODS =====
    getCurrentTime() {
        return new Date().toLocaleTimeString([], { 
            hour: '2-digit', 
            minute: '2-digit' 
        });
    }
    
    highlightCode(element) {
        // Highlight code blocks using Prism.js
        const codeBlocks = element.querySelectorAll('pre code');
        codeBlocks.forEach(block => {
            Prism.highlightElement(block);
        });
    }
    
    showNotification(message, type = 'info') {
        // Simple notification system
        const notification = document.createElement('div');
        notification.className = `notification notification-${type}`;
        notification.innerHTML = `
            <div class="notification-content">
                <span class="notification-message">${message}</span>
                <button class="notification-close">&times;</button>
            </div>
        `;
        
        // Add to page
        document.body.appendChild(notification);
        
        // Auto remove after 5 seconds
        setTimeout(() => {
            if (notification.parentNode) {
                notification.remove();
            }
        }, 5000);
        
        // Manual close
        notification.querySelector('.notification-close').addEventListener('click', () => {
            notification.remove();
        });
        
        // Add styles if not already added
        if (!document.querySelector('#notification-styles')) {
            const styles = document.createElement('style');
            styles.id = 'notification-styles';
            styles.textContent = `
                .notification {
                    position: fixed;
                    top: 20px;
                    right: 20px;
                    max-width: 400px;
                    background: var(--surface-color);
                    border: 1px solid var(--border-color);
                    border-radius: var(--border-radius);
                    box-shadow: var(--shadow-lg);
                    z-index: 10000;
                    animation: slideInRight 0.3s ease-out;
                }
                .notification-success { border-left: 4px solid var(--success-color); }
                .notification-error { border-left: 4px solid var(--error-color); }
                .notification-warning { border-left: 4px solid var(--warning-color); }
                .notification-info { border-left: 4px solid var(--info-color); }
                .notification-content {
                    display: flex;
                    align-items: center;
                    justify-content: space-between;
                    padding: var(--spacing-md);
                    color: var(--text-primary);
                }
                .notification-close {
                    background: none;
                    border: none;
                    color: var(--text-muted);
                    cursor: pointer;
                    font-size: 1.2rem;
                    padding: 0;
                    margin-left: var(--spacing-sm);
                }
                .notification-close:hover { color: var(--text-primary); }
                @keyframes slideInRight {
                    from { transform: translateX(100%); opacity: 0; }
                    to { transform: translateX(0); opacity: 1; }
                }
            `;
            document.head.appendChild(styles);
        }
    }
    
    showError(message) {
        this.showNotification(message, 'error');
        this.hideLoadingOverlay();
    }
    
    showLoadingOverlay() {
        this.elements.loadingOverlay.style.display = 'flex';
    }
    
    hideLoadingOverlay() {
        this.elements.loadingOverlay.style.display = 'none';
    }
    
    handleResize() {
        // Handle responsive design changes
        this.scrollToBottom();
    }
}

// ===== INITIALIZE APPLICATION =====
document.addEventListener('DOMContentLoaded', () => {
    console.log('🎯 DOM loaded, initializing Agentic AI...');
    window.agenticAI = new AgenticAI();
});

// ===== GLOBAL ERROR HANDLING =====
window.addEventListener('error', (event) => {
    console.error('Global error:', event.error);
    if (window.agenticAI) {
        window.agenticAI.showError('An unexpected error occurred. Please refresh the page.');
    }
});

// ===== SERVICE WORKER REGISTRATION (Optional) =====
if ('serviceWorker' in navigator) {
    window.addEventListener('load', () => {
        // Uncomment if you want to add PWA support
        // navigator.serviceWorker.register('/sw.js')
        //     .then(registration => console.log('SW registered:', registration))
        //     .catch(registrationError => console.log('SW registration failed:', registrationError));
    });
}
