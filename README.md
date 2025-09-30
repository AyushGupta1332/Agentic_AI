# Agentic AI Assistant 🤖

A powerful, intelligent AI assistant built with Flask and powered by Groq's LLaMA models. This agentic AI system can autonomously decide which tools to use, search the web, fetch financial data, and maintain conversation memory to provide comprehensive, contextual responses.

Note: We are using GROQ API and GROQ decommissioned some older models and replace them with the new one. So make sure to make replace the names of the older model names to the newer models in the code.

![Python](https://img.shields.io/badge/python-v3.8+-blue.svg)
![Flask](https://img.shields.io/badge/flask-v2.3.3-green.svg)
![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Status](https://img.shields.io/badge/status-active-success.svg)

## 🌟 Features

### 🚀 **New Advanced Capabilities (Latest Update)**
- **Real-Time Data Streams**: Continuous live updates for financial markets, news monitoring, and website change detection.
- **Dynamic Tool Discovery**: Automatically analyzes queries and can create brand new tools on-the-fly to handle novel tasks.
- **Advanced Analytics Engine**: Tracks user interactions, analyzes complexity trends, and provides personalized recommendations.
- **Intelligent Cache System**: Predicts and caches likely next queries for faster responses.
- **Adaptive Response Generator**: Personalizes responses based on sentiment, complexity, and conversation history.
- **Proactive Task Manager**: Detects patterns and offers automation suggestions, monitoring, and knowledge base creation.
- **Enhanced Multi-Agent Pipeline**: Integrates Research, Analysis, and Creative agents with improved orchestration and synthesis.


### 🤖 **Multi-Agent Orchestration**
- **Research Agent**: Handles fact-finding and news exploration
- **Analysis Agent**: Performs financial analysis and structured insights
- **Creative Agent**: Generates stories, articles, poems, and brainstorming ideas
- **Agent Orchestrator**: Selects the most suitable agent automatically and synthesizes results

### 🔍 **Enhanced Query Understanding**
- **Classification System**: Detects if a query is casual, financial, social media, news, or general web
- **Execution Plan**: Dynamically decides which tools to invoke
- **Casual Talk Handling**: Responds naturally to greetings and small talk

### 🛡️ **Improved Error Handling & Fallbacks**
- **Automatic fallback**: If a specialized agent fails, falls back to direct tool execution
- **Graceful responses**: Provides alternative suggestions when results are limited

### 📚 **Memory & Contextual Awareness**
- **Persistent Memory with ChromaDB**: Stores user queries and AI responses
- **Semantic Retrieval**: Retrieves past context for continuity
- **Conversation Manager**: Maintains per-user chat history

### 📡 **Real-time Status Updates**
- Sends live progress updates (e.g., analyzing, running tools, synthesizing) via WebSocket
- Debug-friendly logs for monitoring each step


### 🧠 **Intelligent Agent System**
- **Autonomous Tool Selection**: AI decides which tools to use based on user queries
- **Multi-step Reasoning**: Complex queries are broken down and processed systematically
- **Context Awareness**: Maintains conversation history for coherent interactions

### 🔧 **Powerful Tool Integration**
- **🌐 Web Search**: Real-time web search using DuckDuckGo
- **📰 News Search**: Latest news and current events
- **📈 Financial Data**: Stock prices and financial information via Yahoo Finance
- **🧠 Memory System**: Persistent conversation memory using ChromaDB

### 💻 **Modern Web Interface**
- **Real-time Chat**: WebSocket-based live communication
- **Responsive Design**: Works seamlessly on desktop and mobile
- **Markdown Support**: Rich text formatting with code highlighting
- **Debug Panel**: Developer tools for monitoring AI processes
- **Status Updates**: Live progress tracking during AI processing

## 🚀 Quick Start

### Prerequisites
- Python 3.8 or higher
- pip package manager
- Groq API key ([Get one here](https://console.groq.com/))

### Installation

1. **Clone the repository**

git clone https://github.com/AyushGupta1332/Agentic_AI.git
cd Agentic_AI


2. **Install dependencies**

pip install -r requirements.txt


3. **Set up your API key**
Edit `main.py` and replace the placeholder with your Groq API key:

GROQ_API_KEY = "your-groq-api-key-here"


4. **Run the application**

5. python main.py
 
6. **Open your browser**
Navigate to `http://localhost:5000`

## 🏗️ Project Structure

Agentic_AI/
├── main.py # Main Flask application with all backend logic
├── templates/
│ ├── base.html # Base HTML template
│ └── index.html # Main chat interface
├── static/
│ ├── css/
│ │ └── style.css # Modern UI styling
│ └── js/
│ └── app.js # Frontend JavaScript with SocketIO
├── chroma_db/ # ChromaDB storage (auto-created)
├── requirements.txt # Python dependencies
└── README.md # This file


## 🔄 How It Works

### 1. **Query Analysis**
When you send a message, the AI agent:
- Analyzes your query using Groq's LLaMA 70B model
- Determines which tools (if any) are needed
- Creates an execution plan

### 2. **Tool Execution**
The agent can use multiple tools:
- **Web Search**: For general information and current events
- **News Search**: For latest news and breaking updates  
- **Financial Tool**: For stock prices and market data
- Tools run in parallel for maximum efficiency

### 3. **Information Synthesis**
- Combines data from multiple sources
- Resolves conflicts between sources
- Generates comprehensive, well-structured responses
- Provides confidence scores and source attribution

### 4. **Memory Management**
- Stores conversation history in ChromaDB
- Uses semantic search for relevant context retrieval
- Maintains user-specific conversation threads

## 🎯 Usage Examples

### General Questions

User: What's the latest news about artificial intelligence?
AI: [Uses news search tool] → Provides latest AI news with sources

### Financial Queries

User: What's Apple's current stock price?
AI: [Uses financial tool] → Shows AAPL stock data and analysis

### Research Questions

User: How does quantum computing work?
AI: [Uses web search tool] → Comprehensive explanation with sources


### Complex Multi-tool Queries

User: What's the impact of recent AI developments on tech stocks?
AI: [Uses news search + financial tools] → Combined analysis


## 🛠️ Technical Stack

### Backend
- **Flask + SocketIO**: Real-time web framework
- **Groq API**: LLaMA 70B/8B models for intelligence
- **ChromaDB**: Vector database for conversation memory
- **DuckDuckGo Search**: Web and news search
- **Yahoo Finance**: Financial data retrieval

### Frontend
- **Modern CSS**: Dark theme with smooth animations
- **Real-time Updates**: Live status and progress tracking
- **Markdown Rendering**: Rich text display with code highlighting
- **Responsive Design**: Mobile-first approach

## 🔧 Configuration

### API Keys
- Get your Groq API key from [Groq Console](https://console.groq.com/)
- Replace the placeholder in `main.py`:

GROQ_API_KEY = "your-actual-groq-api-key"

### Environment Variables (Optional)

export GROQ_API_KEY="your-groq-api-key"


## 🚦 API Features

- **Health Check**: `GET /health`
- **Real-time Chat**: WebSocket at `/socket.io/`
- **Status Updates**: Live processing updates
- **Debug Information**: Development insights
- **Conversation Management**: History and memory

## 🎨 Screenshots

### Main Chat Interface
- Modern dark theme with gradient backgrounds
- Real-time typing indicators and status updates
- Responsive design for all screen sizes

### Debug Panel
- Live tool execution monitoring
- Performance metrics and confidence scores
- Source attribution and processing details

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📝 Development

### Adding New Tools
1. Create a class inheriting from `BaseTool`
2. Implement the `execute` method
3. Add to the `Agent`'s tool list
4. Update the schema in `QueryAnalysisService`

### Debug Mode
Enable debug mode in the UI to see:
- Tool execution details
- Processing timestamps
- Raw API responses
- Error traces

## 🔒 Security

- **API Key Security**: Never commit API keys to version control
- **Data Privacy**: Conversation history stored locally
- **Input Validation**: Pydantic models ensure data integrity
- **Error Handling**: Comprehensive error management

## 📊 System Requirements

- **RAM**: Minimum 4GB (8GB recommended)
- **Storage**: 1GB free space
- **Network**: Internet connection required
- **Browser**: Modern browser with WebSocket support

## 🐛 Troubleshooting

### Common Issues
1. **API Key Error**: Ensure your Groq API key is valid
2. **Port Conflict**: Change port in `main.py` if 5000 is occupied
3. **Installation Issues**: Use `pip install --upgrade pip` and retry
4. **Browser Issues**: Clear cache and ensure JavaScript is enabled

### Getting Help
- Check the [Issues](https://github.com/AyushGupta1332/Agentic_AI/issues) page
- Create a new issue with detailed error information
- Include system information and error logs

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **Groq**: For providing fast LLM inference
- **ChromaDB**: For the excellent vector database
- **Flask Community**: For the robust web framework
- **DuckDuckGo**: For search API access

## 📞 Support

For support and questions:
- 📧 Email: ayushranjan8901@gmail.com
- 🐛 Issues: [GitHub Issues](https://github.com/AyushGupta1332/Agentic_AI/issues)
- 💬 Discussions: [GitHub Discussions](https://github.com/AyushGupta1332/Agentic_AI/discussions)

---

**Made by Ayush Gupta**

*⭐ Star this repository if you find it useful!*

## 📦 Requirements

Create a `requirements.txt` file with the following content:

flask==2.3.3
flask-socketio==5.3.6
python-socketio==5.8.0
eventlet==0.33.3
pydantic==2.4.2
httpx==0.25.0
duckduckgo-search==3.9.6
yfinance==0.2.23
groq==0.4.1
chromadb==0.4.15
sentence-transformers==2.2.2

## 🚀 Installation Command

pip install -r requirements.txt

*Note: Future Updates will come soon. 
