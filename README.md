# 🤖 Agentic AI Assistant

[![Python](https://img.shields.io/badge/python-v3.10+-blue.svg)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/flask-v2.3.3-green.svg)](https://flask.palletsprojects.com/)
[![Tailwind CSS](https://img.shields.io/badge/tailwind-v3.0+-38BDF8.svg)](https://tailwindcss.com/)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Status](https://img.shields.io/badge/status-active-success.svg)](https://github.com/AyushGupta1332/Agentic_AI)

> A powerful, intelligent AI assistant with autonomous tool selection, multi-agent orchestration, persistent memory, and a stunning modern web interface.

![Agentic AI Banner](https://via.placeholder.com/1200x300/4F46E5/FFFFFF?text=Agentic+AI+Assistant)

---

## ✨ What's New in Latest Version

### 🎨 Modern Frontend Redesign
- **Tailwind CSS 3.0+**: Fully redesigned with utility-first CSS framework
- **Dark Mode**: Complete dark/light theme with localStorage persistence
- **Alpine.js Integration**: Lightweight reactivity for smooth interactions
- **Responsive Design**: Mobile-first approach, works beautifully on all devices
- **Enhanced UX**: Smooth animations, hover effects, and gradient backgrounds

### 🔧 Backend-Frontend Integration Fixes
- **Socket.IO Event Synchronization**: Fixed all event name mismatches
- **Real-time Updates**: Live status updates during query processing
- **Connection Management**: Visual connection status with auto-reconnect
- **Clear History Feature**: Properly integrated conversation clearing

### 📱 User Interface Enhancements
- **Hero Welcome Section**: Beautiful gradient hero with capability cards
- **Quick Starter Questions**: One-click example queries
- **Message Bubbles**: Modern chat interface with gradient user messages
- **Toast Notifications**: Non-intrusive success/error notifications
- **Character Counter**: Real-time character count (0/2000)
- **Loading Animations**: Smooth pulse effects during processing

---

## 🌟 Core Features

### 🚀 Advanced AI Capabilities

#### **Multi-Agent Orchestration**
The system employs specialized AI agents that automatically collaborate:
- 🔬 **Research Agent**: Web search, fact-checking, news aggregation
- 📊 **Analysis Agent**: Financial analysis, data insights, trend detection
- ✨ **Creative Agent**: Content generation, storytelling, brainstorming
- 🎯 **Agent Orchestrator**: Intelligent agent selection and result synthesis

#### **Intelligent Tool Discovery**
- **Dynamic Tool Creation**: Generates new tools on-the-fly for novel tasks
- **Autonomous Tool Selection**: Analyzes queries and picks the right tools
- **Tool Chain Execution**: Orchestrates multiple tools for complex queries

#### **Advanced Memory System**
- **ChromaDB Vector Store**: Semantic search over past conversations
- **Contextual Retrieval**: Remembers previous discussions for continuity
- **Per-User History**: Maintains separate conversation threads
- **Embedding Model**: `all-MiniLM-L6-v2` for efficient semantic matching

### 🔍 Enhanced Query Processing

```
User Query → Classification → Agent Selection → Tool Chain → Response Generation → Personalization
```

- **Query Classification**: Detects intent (casual, financial, news, general)
- **Execution Planning**: Builds optimal tool chain
- **Real-time Status**: LiveSocket updates during processing
- **Adaptive Responses**: Personalized based on history and sentiment

### 📚 Persistent Features

- **Conversation Memory**: ChromaDB stores all interactions
- **Analytics Engine**: Tracks complexity, topics, sentiment trends
- **Intelligent Cache**: Predicts and pre-caches likely follow-up queries
- **Proactive Suggestions**: Offers automation based on detected patterns

### 🌐 Real-Time Communication

- **WebSocket (Socket.IO)**: Bi-directional real-time messaging
- **Event-Driven Architecture**: Clean separation of concerns
- **Status Broadcasting**: Live updates on query processing steps
- **Auto-Reconnection**: Resilient connection management

---

## 🏗️ Project Architecture

### Directory Structure

```
Agentic_AI-main/
│
├── 📁 app/                        # Main application package
│   ├── 📁 agents/                 # AI Agent implementations
│   │   ├── base.py               # Base agent class
│   │   ├── research.py           # Research specialist
│   │   ├── analysis.py           # Analysis specialist
│   │   ├── creative.py           # Creative specialist
│   │   ├── orchestrator.py       # Agent coordinator
│   │   └── enhanced_agent.py     # Enhanced agent with all features
│   │
│   ├── 📁 services/               # Core business logic
│   │   ├── memory.py             # ChromaDB memory manager
│   │   ├── analytics.py          # Usage analytics tracker
│   │   ├── cache.py              # Intelligent caching system
│   │   ├── proactive.py          # Proactive task suggestions
│   │   ├── query_analysis.py    # Query classification
│   │   ├── response.py           # Response personalization
│   │   ├── synthesis.py          # Multi-agent synthesis
│   │   └── processing.py         # Stream processing
│   │
│   ├── 📁 tools/                  # AI Tools
│   │   ├── base.py               # Base tool class
│   │   ├── search.py             # Web search (DuckDuckGo)
│   │   ├── finance.py            # Financial data (yfinance)
│   │   └── discovery.py          # Dynamic tool creation
│   │
│   ├── 📁 utils/                  # Utilities
│   │   ├── logging_config.py     # Logging setup
│   │   └── helpers.py            # Helper functions
│   │
│   ├── __init__.py               # App factory
│   ├── routes.py                 # Flask routes & Socket.IO events
│   ├── connection.py             # Connection management
│   └── models.py                 # Data models
│
├── 📁 templates/                  # Jinja2 HTML templates
│   ├── base.html                 # Base template with Tailwind config
│   └── index.html                # Main chat interface
│
├── 📁 static/                     # Frontend assets
│   ├── 📁 css/
│   │   └── style.css             # Custom CSS (animations, overrides)
│   └── 📁 js/
│       └── app.js                # Frontend logic (~415 lines, refactored)
│
├── 📁 tests/                      # Automated tests
│   ├── conftest.py               # Test configuration
│   ├── test_agents.py            # Agent tests
│   ├── test_services.py          # Service tests
│   └── test_tools.py             # Tool tests
│
├── 📁 chroma_db/                  # Vector database storage (auto-created)
│
├── 📄 config.py                   # Configuration (API keys, settings)
├── 📄 main.py                     # Application entry point
├── 📄 requirements.txt            # Python dependencies
├── 📄 LICENSE                     # MIT License
│
├── 📄 README.md                   # This file
├── 📄 CHANGES_SUMMARY.md          # Frontend modernization details
├── 📄 BACKEND_FRONTEND_FIXES.md   # Integration fixes documentation
└── 📄 DESIGN_SYSTEM.md            # UI/UX design system guide
```

### Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                      User (Browser)                         │
│          HTML5 • CSS3 • JavaScript • Socket.IO              │
└───────────────────────┬─────────────────────────────────────┘
                        │ WebSocket (Real-time)
                        ↓
┌─────────────────────────────────────────────────────────────┐
│                   Flask Application                         │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  Routes & Socket.IO Handlers (routes.py)            │   │
│  └────────────────────┬────────────────────────────────┘   │
│                       ↓                                     │
│  ┌─────────────────────────────────────────────────────┐   │
│  │         Enhanced Agent (enhanced_agent.py)          │   │
│  │  • Query Analysis   • Agent Orchestration           │   │
│  │  • Tool Selection   • Response Synthesis            │   │
│  └────┬──────────────┬──────────────┬──────────────┬───┘   │
│       ↓              ↓              ↓              ↓       │
│  ┌────────┐    ┌──────────┐   ┌─────────┐   ┌─────────┐  │
│  │Research│    │ Analysis │   │Creative │   │ Tools   │  │
│  │ Agent  │    │  Agent   │   │  Agent  │   │ System  │  │
│  └────────┘    └──────────┘   └─────────┘   └────┬────┘  │
│                                                     ↓       │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  Services Layer                                      │  │
│  │  • Memory (ChromaDB)  • Analytics  • Cache          │  │
│  │  • Proactive Tasks    • Response Personalization    │  │
│  └──────────────────────────────────────────────────────┘  │
└───────────────────────┬─────────────────────────────────────┘
                        ↓
         ┌──────────────┴──────────────┐
         ↓                             ↓
┌──────────────────┐        ┌──────────────────────┐
│   Groq API       │        │   External APIs      │
│ (LLaMA 3 Models) │        │ • DuckDuckGo Search  │
│                  │        │ • Yahoo Finance      │
└──────────────────┘        └──────────────────────┘
```

---

## 🚀 Quick Start Guide

### Prerequisites

Make sure you have the following installed:

- **Python 3.10+** (tested on 3.13)
- **pip** (Python package manager)
- **Groq API Key** ([Get one free here](https://console.groq.com/))

### Installation Steps

#### 1️⃣ Clone the Repository

```bash
git clone https://github.com/AyushGupta1332/Agentic_AI.git
cd Agentic_AI-main
```

#### 2️⃣ Install Python Dependencies

```bash
pip install -r requirements.txt
```

**Dependencies installed:**
- `flask` - Web framework
- `flask-socketio` - WebSocket support
- `groq` - Groq API client
- `chromadb` - Vector database
- `sentence-transformers` - Embedding models
- `duckduckgo-search` - Web search
- `yfinance` - Financial data
- `pytest` - Testing framework
- And more...

#### 3️⃣ Configure API Key

**Method A: Environment Variable (Recommended)**

```bash
# Windows PowerShell
$env:GROQ_API_KEY="gsk_your_api_key_here"

# Linux/Mac/Git Bash
export GROQ_API_KEY="gsk_your_api_key_here"
```

**Method B: .env File**

Create a `.env` file in the project root:

```env
GROQ_API_KEY=gsk_your_api_key_here
SECRET_KEY=your-secret-key-change-in-production
```

#### 4️⃣ Run the Application

```bash
python main.py
```

**Expected output:**
```
🚀 Starting Enhanced Agentic AI Server...
📱 Access the interface at http://localhost:5000
* Running on http://127.0.0.1:5000
```

#### 5️⃣ Open Your Browser

Navigate to: **http://localhost:5000**

You should see the beautiful Agentic AI interface! 🎉

---

## 🧪 Testing

### Run All Tests

```bash
python -m pytest tests/ -v
```

### Run Specific Test Suites

```bash
# Test agents
python -m pytest tests/test_agents.py -v

# Test services
python -m pytest tests/test_services.py -v

# Test tools
python -m pytest tests/test_tools.py -v
```

### Test Coverage

```bash
pytest --cov=app tests/
```

---

## 🎨 Frontend Design System

### Technologies Used

- **Tailwind CSS 3.0+**: Utility-first CSS framework (via CDN)
- **Alpine.js 3.x**: Lightweight JavaScript framework for reactivity
- **Socket.IO Client**: Real-time WebSocket communication
- **Marked.js**: Markdown to HTML conversion
- **Prism.js**: Syntax highlighting for code blocks
- **Feather Icons**: Beautiful open-source icons
- **Google Fonts**: Inter (body) & JetBrains Mono (code)

### Color Palette

#### Light Mode
- **Primary**: Indigo (#4F46E5) → Violet (#7C3AED)
- **Background**: White (#FFFFFF), Gray-50 (#F9FAFB)
- **Text**: Gray-900 (#111827)

#### Dark Mode
- **Primary**: Indigo (#6366F1) → Violet (#8B5CF6)
- **Background**: Gray-900 (#111827), Gray-800 (#1F2937)
- **Text**: White (#FFFFFF)

### Key UI Components

#### 💬 Message Bubbles
- **User**: Gradient blue/purple bubble (right-aligned)
- **AI**: Clean white/dark background (left-aligned)
- **Animations**: Smooth slide-in on message arrival

#### 🎯 Status Badge
- **Connected**: Green pulsing indicator
- **Disconnected**: Red indicator
- **Processing**: Blue with loading animation

#### 🎨 Cards
- **Hover Effect**: Lift up + shadow increase
- **Click**: Slight scale down for feedback
- **Transitions**: Smooth 200-300ms

For complete design documentation, see [DESIGN_SYSTEM.md](DESIGN_SYSTEM.md)

---

## 🛠️ Technical Stack

### Backend

| Technology | Purpose | Version |
|------------|---------|---------|
| **Python** | Core language | 3.10+ |
| **Flask** | Web framework | 2.3.3 |
| **Flask-SocketIO** | WebSocket support | Latest |
| **Groq SDK** | LLM API client | Latest |
| **ChromaDB** | Vector database | Latest |
| **Sentence Transformers** | Embeddings | Latest |

### Frontend

| Technology | Purpose | Source |
|------------|---------|--------|
| **Tailwind CSS** | Styling framework | CDN |
| **Alpine.js** | Reactivity | CDN |
| **Socket.IO Client** | WebSocket | CDN |
| **Marked.js** | Markdown parser | CDN |
| **Prism.js** | Code highlighting | CDN |

### External APIs

- **Groq API**: LLaMA 3 language models (70B & 8B)
- **DuckDuckGo API**: Web search
- **Yahoo Finance**: Stock data and financial information

---

## 📊 Performance Metrics

### Code Optimization

| File | Before | After | Change |
|------|--------|-------|--------|
| `app.js` | 865 lines | 415 lines | ✅ -52% |
| `style.css` | 1364 lines | 150 lines | ✅ -89% |
| `index.html` | 309 lines | 475 lines | ⚡ Enhanced |
| `base.html` | 90 lines | 216 lines | ⚡ Enhanced |

### Load Performance

- **Initial Load**: < 2 seconds
- **JavaScript**: ~35KB (gzipped)
- **CSS**: ~50KB (gzipped)
- **Total Assets**: ~185KB

### Core Web Vitals

- **LCP** (Largest Contentful Paint): < 2.5s ✅
- **FID** (First Input Delay): < 100ms ✅
- **CLS** (Cumulative Layout Shift): < 0.1 ✅

---

## 🔧 Configuration

### Environment Variables

Create a `.env` file or set these in your environment:

```env
# Required
GROQ_API_KEY=gsk_your_groq_api_key

# Optional
SECRET_KEY=your-flask-secret-key
CHROMA_DB_PATH=./chroma_db
EMBEDDING_MODEL=all-MiniLM-L6-v2
```

### Config.py Settings

```python
# API Keys
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

# Flask Config
SECRET_KEY = os.getenv("SECRET_KEY", "default-secret-key")

# ChromaDB Config
CHROMA_DB_PATH = "./chroma_db"
EMBEDDING_MODEL = "all-MiniLM-L6-v2"
```

---

## 🐛 Troubleshooting

### Common Issues

#### ❌ "Socket.IO not connecting"

**Solution:**
1. Check browser console (F12) for errors
2. Verify server is running on port 5000
3. Clear browser cache (Ctrl+Shift+Delete)
4. Try hard refresh (Ctrl+F5)

#### ❌ "Queries get stuck / no response"

**Solution:**
1. Verify `GROQ_API_KEY` is set correctly
2. Check server logs for API errors
3. Ensure event names match (see `BACKEND_FRONTEND_FIXES.md`)

#### ❌ "ChromaDB import error"

**Solution:**
```bash
pip uninstall chromadb
pip install chromadb --no-cache-dir
```

#### ❌ "Dark mode not persisting"

**Solution:**
1. Check browser localStorage is enabled
2. Clear site data and try again
3. Ensure Alpine.js is loaded (check DevTools → Network)

### Enable Debug Mode

In `main.py`, the debug mode is enabled by default:

```python
socketio.run(app, debug=True, use_reloader=False, port=5000)
```

Check terminal logs for detailed error messages.

---

## 📖 Additional Documentation

- **[CHANGES_SUMMARY.md](CHANGES_SUMMARY.md)**: Complete list of frontend modernization changes
- **[BACKEND_FRONTEND_FIXES.md](BACKEND_FRONTEND_FIXES.md)**: Socket.IO integration fixes
- **[DESIGN_SYSTEM.md](DESIGN_SYSTEM.md)**: UI/UX design tokens and component guide

---

## 🤝 Contributing

We welcome contributions! Here's how to get started:

### 1. Fork the Repository

Click the "Fork" button on GitHub.

### 2. Clone Your Fork

```bash
git clone https://github.com/YOUR_USERNAME/Agentic_AI.git
cd Agentic_AI-main
```

### 3. Create a Feature Branch

```bash
git checkout -b feature/amazing-new-feature
```

### 4. Make Your Changes

- Follow existing code style
- Add tests for new features
- Update documentation as needed

### 5. Run Tests

```bash
python -m pytest tests/ -v
```

### 6. Commit and Push

```bash
git add .
git commit -m "Add amazing new feature"
git push origin feature/amazing-new-feature
```

### 7. Create Pull Request

Go to GitHub and create a Pull Request from your branch.

---

## 📄 License

This project is licensed under the **MIT License**.

```
MIT License

Copyright (c) 2024 Ayush Gupta

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

See [LICENSE](LICENSE) for full details.

---

## 🌟 Acknowledgments

### Technologies & Libraries

- **Groq**: For the amazing LLaMA API
- **Tailwind CSS**: For the beautiful utility-first CSS framework
- **Alpine.js**: For lightweight JavaScript reactivity
- **Flask**: For the robust Python web framework
- **ChromaDB**: For the powerful vector database

### Inspiration

This project was inspired by the need for an intelligent, autonomous AI assistant that can:
- 🧠 Think for itself and select the right tools
- 💬 Remember past conversations
- 🎨 Provide a beautiful user experience
- ⚡ Respond in real-time

---

## 📞 Support & Contact

### Get Help

- **📧 Email**: [ayushranjan8901@gmail.com](mailto:ayushranjan8901@gmail.com)
- **🐛 Issues**: [GitHub Issues](https://github.com/AyushGupta1332/Agentic_AI/issues)
- **💬 Discussions**: [GitHub Discussions](https://github.com/AyushGupta1332/Agentic_AI/discussions)

### Stay Updated

- **⭐ Star this repository** to show your support!
- **👀 Watch** for updates and new releases
- **🍴 Fork** to create your own version

---

## 🎯 Roadmap

### Upcoming Features

- [ ] **Voice Input**: Speak to the AI assistant
- [ ] **Multi-language Support**: Translate conversations
- [ ] **Export Conversations**: Download as PDF/Markdown
- [ ] **Custom Themes**: User-created color schemes
- [ ] **Plugin System**: Install third-party tools
- [ ] **Mobile App**: Native iOS/Android apps
- [ ] **Collaborative Mode**: Share conversations with team

### In Progress

- [x] Frontend modernization with Tailwind CSS ✅
- [x] Real-time Socket.IO integration ✅
- [x] Multi-agent architecture ✅
- [x] Dark mode support ✅
- [x] ChromaDB memory system ✅

---

<div align="center">

### Made with ❤️ by Ayush Gupta

**⭐ If you find this project useful, please consider giving it a star!**

[![GitHub stars](https://img.shields.io/github/stars/AyushGupta1332/Agentic_AI?style=social)](https://github.com/AyushGupta1332/Agentic_AI/stargazers)
[![GitHub forks](https://img.shields.io/github/forks/AyushGupta1332/Agentic_AI?style=social)](https://github.com/AyushGupta1332/Agentic_AI/network/members)

---

**Happy Coding! 🚀**

</div>
