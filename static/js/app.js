// ===== MODERN AGENTIC AI APPLICATION WITH TAILWIND CSS =====
class AgenticAI {
    constructor() {
        this.socket = null;
        this.isConnected = false;
        this.messageHistory = [];
        this.isInitialized = false;
        
        this.quickStarters = [
            "What's the latest news in tech?",
            "Search for information about AI",
            "Get me financial data for AAPL",
            "Tell me about recent market trends",
            "What are the top trending topics?",
            "Analyze the current weather forecast"
        ];

        this.elements = this.initializeElements();
        this.init();
    }

    initializeElements() {
        return {
            app: document.getElementById('app'),
            loadingScreen: document.getElementById('loading-screen'),
            connectionBadge: document.getElementById('connection-badge'),
            connectionText: document.querySelector('.connection-text'),
            clearBtn: document.getElementById('clear-btn'),
            messagesArea: document.getElementById('messages-area'),
            welcomeScreen: document.getElementById('welcome-screen'),
            messagesContainer: document.getElementById('messages-container'),
            quickStarters: document.getElementById('quick-starters'),
            messageInput: document.getElementById('message-input'),
            messageForm: document.getElementById('message-form'),
            sendBtn: document.getElementById('send-btn'),
            charCount: document.getElementById('char-count'),
            userMessageTemplate: document.getElementById('user-message-template'),
            aiMessageTemplate: document.getElementById('ai-message-template'),
            errorMessageTemplate: document.getElementById('error-message-template'),
            sourceLinkTemplate: document.getElementById('source-link-template'),
            toastContainer: document.getElementById('toast-container')
        };
    }

    init() {
        console.log('🚀 Initializing Agentic AI...');
        this.setupEventListeners();
        this.setupQuickStarters();
        this.connectSocket();

        setTimeout(() => {
            if (!this.isInitialized) {
                this.completeInitialization();
            }
        }, 3000);
    }

    completeInitialization() {
        if (this.isInitialized) return;
        this.isInitialized = true;
        this.hideLoadingScreen();
    }

    hideLoadingScreen() {
        if (this.elements.loadingScreen) {
            this.elements.loadingScreen.style.opacity = '0';
            setTimeout(() => {
                this.elements.loadingScreen.style.display = 'none';
            }, 300);
        }
    }

    setupEventListeners() {
        if (this.elements.messageForm) {
            this.elements.messageForm.addEventListener('submit', (e) => {
                e.preventDefault();
                this.sendMessage();
            });
        }

        if (this.elements.messageInput) {
            this.elements.messageInput.addEventListener('input', (e) => {
                const length = e.target.value.length;
                if (this.elements.charCount) {
                    this.elements.charCount.textContent = `${length}/2000`;
                }
            });
        }

        if (this.elements.clearBtn) {
            this.elements.clearBtn.addEventListener('click', () => {
                this.clearConversation();
            });
        }
    }

    setupQuickStarters() {
        if (!this.elements.quickStarters) return;

        this.quickStarters.forEach(question => {
            const button = document.createElement('button');
            button.type = 'button';
            button.className = `w-full text-left p-3 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg hover:border-indigo-500 dark:hover:border-indigo-400 hover:shadow-md transition-all duration-200 text-sm text-gray-700 dark:text-gray-300 hover:text-indigo-600 dark:hover:text-indigo-400 group`;
            
            button.innerHTML = `
                <div class="flex items-center gap-2">
                    <svg class="w-4 h-4 text-gray-400 group-hover:text-indigo-500 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z" />
                    </svg>
                    <span class="line-clamp-2">${this.escapeHtml(question)}</span>
                </div>
            `;
            
            button.addEventListener('click', () => {
                this.elements.messageInput.value = question;
                this.sendMessage();
            });
            
            this.elements.quickStarters.appendChild(button);
        });
    }

    async sendMessage() {
        const message = this.elements.messageInput.value.trim();
        
        if (!message) {
            this.showToast('Please enter a message', 'warning');
            return;
        }

        if (!this.isConnected) {
            this.showToast('Not connected to server. Please try again.', 'error');
            return;
        }

        if (this.elements.welcomeScreen) {
            this.elements.welcomeScreen.style.display = 'none';
        }

        this.addUserMessage(message);
        this.elements.messageInput.value = '';
        this.elements.charCount.textContent = '0/2000';

        this.elements.sendBtn.disabled = true;
        this.elements.sendBtn.querySelector('.send-icon').classList.add('hidden');
        this.elements.sendBtn.querySelector('.loading-icon').classList.remove('hidden');

        try {
            if (this.socket) {
                this.socket.emit('send_message', { message: message });
            }
        } catch (error) {
            console.error('Error sending message:', error);
            this.showToast('Failed to send message', 'error');
            this.elements.sendBtn.disabled = false;
            this.elements.sendBtn.querySelector('.send-icon').classList.remove('hidden');
            this.elements.sendBtn.querySelector('.loading-icon').classList.add('hidden');
        }
    }

    addUserMessage(text) {
        const clone = this.elements.userMessageTemplate.content.cloneNode(true);
        const contentDiv = clone.querySelector('.message-content');
        const timeSpan = clone.querySelector('span');

        contentDiv.textContent = text;
        timeSpan.textContent = this.getFormattedTime();

        this.elements.messagesContainer.appendChild(clone);
        this.scrollToBottom();
    }

    addAIMessage(text, sources = []) {
        const clone = this.elements.aiMessageTemplate.content.cloneNode(true);
        const contentDiv = clone.querySelector('.message-content');
        const sourcesDiv = clone.querySelector('.message-sources');
        const timeSpan = clone.querySelector('span');

        try {
            const html = marked(text);
            contentDiv.innerHTML = html;
        } catch (error) {
            contentDiv.textContent = text;
        }

        if (sources && sources.length > 0) {
            sourcesDiv.innerHTML = '';
            sources.forEach(source => {
                const sourceClone = this.elements.sourceLinkTemplate.content.cloneNode(true);
                const link = sourceClone.querySelector('a');
                const titleDiv = sourceClone.querySelector('.source-title');
                const urlDiv = sourceClone.querySelector('.source-url');

                link.href = source.url || '#';
                titleDiv.textContent = source.title || 'Source';
                urlDiv.textContent = source.url || '';

                sourcesDiv.appendChild(sourceClone);
            });
        }

        timeSpan.textContent = this.getFormattedTime();
        this.elements.messagesContainer.appendChild(clone);
        this.scrollToBottom();
    }

    addErrorMessage(text) {
        const clone = this.elements.errorMessageTemplate.content.cloneNode(true);
        const contentDiv = clone.querySelector('.message-content');
        contentDiv.textContent = text;

        this.elements.messagesContainer.appendChild(clone);
        this.scrollToBottom();
    }

    connectSocket() {
        try {
            this.socket = io();

            this.socket.on('connect', () => {
                console.log('✅ Connected to server');
                this.isConnected = true;
                this.updateConnectionBadge('Connected', 'connected');
                this.completeInitialization();
            });

            this.socket.on('disconnect', () => {
                console.log('❌ Disconnected from server');
                this.isConnected = false;
                this.updateConnectionBadge('Disconnected', 'disconnected');
            });

            this.socket.on('final_response', (data) => {
                this.handleResponse(data);
            });

            this.socket.on('error', (error) => {
                console.error('❌ Socket error:', error);
                this.addErrorMessage(error.message || 'An error occurred');
                this.showToast('Error: ' + (error.message || 'Unknown error'), 'error');
            });
        } catch (error) {
            console.error('❌ Socket connection error:', error);
            this.addErrorMessage('Failed to connect to server');
            this.completeInitialization();
        }
    }

    handleResponse(data) {
        this.elements.sendBtn.disabled = false;
        this.elements.sendBtn.querySelector('.send-icon').classList.remove('hidden');
        this.elements.sendBtn.querySelector('.loading-icon').classList.add('hidden');

        if (data.error) {
            this.addErrorMessage(data.error);
            this.showToast(data.error, 'error');
        } else {
            this.addAIMessage(data.text || data.response || '', data.sources || []);
            this.showToast('Response received', 'success');
        }
    }

    updateConnectionBadge(text, status) {
        if (!this.elements.connectionBadge) return;

        this.elements.connectionBadge.className = 'flex items-center gap-2 px-3 py-2 rounded-lg text-sm font-medium transition-colors duration-200';
        
        if (status === 'connected') {
            this.elements.connectionBadge.classList.add('bg-green-50', 'dark:bg-green-900/30', 'text-green-700', 'dark:text-green-300');
        } else if (status === 'connecting') {
            this.elements.connectionBadge.classList.add('bg-blue-50', 'dark:bg-blue-900/30', 'text-blue-700', 'dark:text-blue-300');
        } else {
            this.elements.connectionBadge.classList.add('bg-red-50', 'dark:bg-red-900/30', 'text-red-700', 'dark:text-red-300');
        }

        if (this.elements.connectionText) {
            this.elements.connectionText.textContent = text;
        }
    }

    clearConversation() {
        if (!confirm('Are you sure you want to clear the conversation? This cannot be undone.')) {
            return;
        }

        this.messageHistory = [];
        this.elements.messagesContainer.innerHTML = '';
        this.elements.welcomeScreen.style.display = 'flex';
        this.showToast('Conversation cleared', 'success');

        if (this.socket) {
            this.socket.emit('clear_history');
        }
    }

    scrollToBottom() {
        setTimeout(() => {
            this.elements.messagesContainer.scrollIntoView({ behavior: 'smooth', block: 'end' });
        }, 100);
    }

    showToast(message, type = 'info') {
        const toast = document.createElement('div');
        toast.className = `px-4 py-3 rounded-lg font-medium text-sm animate-slide-in transition-all duration-300`;

        switch (type) {
            case 'success':
                toast.classList.add('bg-green-50', 'dark:bg-green-900/30', 'text-green-700', 'dark:text-green-300');
                break;
            case 'error':
                toast.classList.add('bg-red-50', 'dark:bg-red-900/30', 'text-red-700', 'dark:text-red-300');
                break;
            case 'warning':
                toast.classList.add('bg-yellow-50', 'dark:bg-yellow-900/30', 'text-yellow-700', 'dark:text-yellow-300');
                break;
            default:
                toast.classList.add('bg-blue-50', 'dark:bg-blue-900/30', 'text-blue-700', 'dark:text-blue-300');
        }

        toast.innerHTML = `
            <div class="flex items-center gap-2">
                ${this.getToastIcon(type)}
                <span>${this.escapeHtml(message)}</span>
            </div>
        `;

        this.elements.toastContainer.appendChild(toast);

        setTimeout(() => {
            toast.style.opacity = '0';
            toast.style.transform = 'translateY(10px)';
            setTimeout(() => toast.remove(), 300);
        }, 3000);
    }

    getToastIcon(type) {
        const icons = {
            success: '<svg class="w-5 h-5" fill="currentColor" viewBox="0 0 20 20"><path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clip-rule="evenodd"/></svg>',
            error: '<svg class="w-5 h-5" fill="currentColor" viewBox="0 0 20 20"><path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clip-rule="evenodd"/></svg>',
            warning: '<svg class="w-5 h-5" fill="currentColor" viewBox="0 0 20 20"><path fill-rule="evenodd" d="M18.101 12.93a1 1 0 00-1.4-1.42L10 14.585 3.299 8.93a1 1 0 00-1.4 1.42l7.776 7.776a1 1 0 001.4 0l11.026-11.026z" clip-rule="evenodd"/></svg>',
        };
        return icons[type] || '';
    }

    getFormattedTime() {
        const now = new Date();
        return now.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    }

    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
}

// Initialize app when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    window.agenticAI = new AgenticAI();
});
