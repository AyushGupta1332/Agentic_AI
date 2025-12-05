# Agentic AI Assistant 🤖

A powerful, intelligent AI assistant built with Flask and powered by Groq's LLaMA models. This agentic AI system can autonomously decide which tools to use, search the web, fetch financial data, and maintain conversation memory to provide comprehensive, contextual responses.

![Python](https://img.shields.io/badge/python-v3.13+-blue.svg)
![Flask](https://img.shields.io/badge/flask-v2.3.3-green.svg)
![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Status](https://img.shields.io/badge/status-active-success.svg)

## 🌟 Features

### 🚀 **Advanced Capabilities**
- **Real-Time Data Streams**: Continuous live updates for financial markets, news monitoring, and website change detection.
- **Dynamic Tool Discovery**: Automatically analyzes queries and can create brand new tools on-the-fly to handle novel tasks.
- **Advanced Analytics Engine**: Tracks user interactions, analyzes complexity trends, and provides personalized recommendations.
- **Intelligent Cache System**: Predicts and caches likely next queries for faster responses.
- **Adaptive Response Generator**: Personalizes responses based on sentiment, complexity, and conversation history.
- **Proactive Task Manager**: Detects patterns and offers automation suggestions, monitoring, and knowledge base creation.

### 🤖 **Multi-Agent Orchestration**
- **Research Agent**: Handles fact-finding and news exploration.
- **Analysis Agent**: Performs financial analysis and structured insights.
- **Creative Agent**: Generates stories, articles, poems, and brainstorming ideas.
- **Agent Orchestrator**: Selects the most suitable agent automatically and synthesizes results.

### 🔍 **Enhanced Query Understanding**
- **Classification System**: Detects if a query is casual, financial, social media, news, or general web.
- **Execution Plan**: Dynamically decides which tools to invoke.
- **Casual Talk Handling**: Responds naturally to greetings and small talk.

### 📚 **Memory & Contextual Awareness**
- **Persistent Memory with ChromaDB**: Stores user queries and AI responses.
- **Semantic Retrieval**: Retrieves past context for continuity.
- **Conversation Manager**: Maintains per-user chat history.

###  **Modern Web Interface**
- **Real-time Chat**: WebSocket-based live communication.
- **Responsive Design**: Works seamlessly on desktop and mobile.
- **Markdown Support**: Rich text formatting with code highlighting.
- **Debug Panel**: Developer tools for monitoring AI processes.

## 🏗️ Project Structure

The project has been refactored into a modular architecture for better scalability and maintainability:

```
Agentic_AI/
├── app/
│   ├── agents/          # Agent logic (Research, Analysis, Creative, Orchestrator)
│   ├── services/        # Core services (Memory, Analytics, Cache, Synthesis)
│   ├── tools/           # Tool definitions (Search, Finance, Discovery)
│   ├── utils/           # Helper functions and logging
│   ├── routes.py        # Flask routes and SocketIO events
│   └── __init__.py      # App factory
├── tests/               # Automated tests
├── templates/           # HTML templates
├── static/              # CSS and JavaScript
├── chroma_db/           # Vector database storage
├── config.py            # Configuration settings
├── main.py              # Application entry point
├── requirements.txt     # Python dependencies
└── README.md            # Documentation
```

## 🚀 Quick Start

### Prerequisites
- Python 3.10 or higher (Tested on 3.13)
- pip package manager
- Groq API key ([Get one here](https://console.groq.com/))

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/AyushGupta1332/Agentic_AI.git
   cd Agentic_AI
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up your API key**
   
   **Option A (Recommended): Environment Variable**
   Set the `GROQ_API_KEY` environment variable in your terminal:
   ```bash
   # Windows PowerShell
   $env:GROQ_API_KEY="your-groq-api-key"
   
   # Linux/Mac
   export GROQ_API_KEY="your-groq-api-key"
   ```

   **Option B: .env file**
   Create a `.env` file in the root directory and add:
   ```
   GROQ_API_KEY=your-groq-api-key
   ```

4. **Run the application**
   ```bash
   python main.py
   ```

5. **Open your browser**
   Navigate to `http://localhost:5000`

## 🧪 Running Tests

The project includes automated tests to ensure reliability.

```bash
# Run all tests
python -m pytest tests

# Run specific test file
python -m pytest tests/test_agents.py
```

## 🛠️ Technical Stack

- **Backend**: Flask, SocketIO (Threading mode), Python 3.13+
- **AI/LLM**: Groq API (LLaMA 3 models)
- **Database**: ChromaDB (Vector Store)
- **Search**: DuckDuckGo Search (ddgs)
- **Finance**: Yahoo Finance (yfinance)
- **Frontend**: HTML5, CSS3, JavaScript (Socket.IO client)

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

##  Support

For support and questions:
- 📧 Email: ayushranjan8901@gmail.com
- 🐛 Issues: [GitHub Issues](https://github.com/AyushGupta1332/Agentic_AI/issues)

---

**Made by Ayush Gupta**

*⭐ Star this repository if you find it useful!*
