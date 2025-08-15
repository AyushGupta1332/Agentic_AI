# main.py
# This script contains the entire backend logic for the agentic AI with Flask UI.
# For a real-world application, it's recommended to split this into multiple files
# as per the structure outlined in the initial plan.

# --- IMPORTS ---
import os
import asyncio
import json
from datetime import datetime
import logging
from typing import List, Dict, Any, Optional, Union
from flask import Flask, render_template, request, jsonify
from flask_socketio import SocketIO, emit, disconnect
import threading
from pydantic import BaseModel, Field
import httpx
from duckduckgo_search import DDGS
import yfinance as yf
from groq import Groq, AsyncGroq
import chromadb
from chromadb.utils import embedding_functions

# --- CONFIGURATION ---
# Hardcoded GROQ API Key
GROQ_API_KEY = "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"

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# --- INITIALIZE FLASK APP ---
app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-change-this-in-production'
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

# --- INITIALIZE SERVICES ---
# Check if the API key is provided before initializing
if not GROQ_API_KEY:
    raise ValueError("GROQ_API_KEY is not set. Please hardcode your API key.")

groq_client = AsyncGroq(api_key=GROQ_API_KEY)

# ChromaDB Client for Memory
# This will create a persistent database in the './chroma_db' directory
chroma_client = chromadb.PersistentClient(path="./chroma_db")

# Default embedding function for ChromaDB
# Using a sentence-transformer model that runs locally
embedding_function = embedding_functions.SentenceTransformerEmbeddingFunction(model_name="all-MiniLM-L6-v2")

# Get or create a collection in ChromaDB
# This collection will store the conversation history
memory_collection = chroma_client.get_or_create_collection(
    name="agentic_memory",
    embedding_function=embedding_function,
    metadata={"hnsw:space": "cosine"}  # Using cosine distance for similarity search
)

# --- Pydantic Schemas for Data Validation ---
class ToolCall(BaseModel):
    name: str
    parameters: Dict[str, Any]

class AgentAction(BaseModel):
    tool_calls: List[ToolCall]
    log: str

# --- TOOLS ---
class BaseTool:
    """Base class for all tools."""
    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description

    async def execute(self, **kwargs) -> Any:
        raise NotImplementedError("Each tool must implement the execute method.")

class WebSearchTool(BaseTool):
    """Tool for performing web searches using DuckDuckGo."""
    def __init__(self):
        super().__init__(
            name="web_search",
            description="Searches the web for information on a given query. Use for general questions, current events, or finding information on a topic."
        )

    async def execute(self, query: str, num_results: int = 5) -> List[Dict[str, str]]:
        logging.info(f"Executing web search for query: {query}")
        try:
            with DDGS() as ddgs:
                results = [r for r in ddgs.text(query, max_results=num_results)]
            
            # Extract relevant information from search results
            formatted_results = []
            for result in results:
                formatted_results.append({
                    "title": result.get('title'),
                    "snippet": result.get('body'),
                    "url": result.get('href')
                })
            return formatted_results
        except Exception as e:
            logging.error(f"Error during web search: {e}")
            return [{"error": str(e)}]

class NewsSearchTool(BaseTool):
    """Tool for searching for recent news articles."""
    def __init__(self):
        super().__init__(
            name="news_search",
            description="Searches for recent news articles on a given topic. Use when the user asks for the latest news."
        )

    async def execute(self, query: str, num_results: int = 5) -> List[Dict[str, str]]:
        logging.info(f"Executing news search for query: {query}")
        try:
            with DDGS() as ddgs:
                results = [r for r in ddgs.news(query, max_results=num_results)]
            
            formatted_results = []
            for result in results:
                formatted_results.append({
                    "title": result.get('title'),
                    "source": result.get('source'),
                    "date": result.get('date'),
                    "url": result.get('url')
                })
            return formatted_results
        except Exception as e:
            logging.error(f"Error during news search: {e}")
            return [{"error": str(e)}]

class FinancialTool(BaseTool):
    """Tool for fetching financial data for a stock ticker."""
    def __init__(self):
        super().__init__(
            name="get_stock_info",
            description="Fetches financial information for a given stock ticker symbol. Use when the user asks about stock prices or financial data."
        )

    async def execute(self, ticker: str) -> Dict[str, Any]:
        logging.info(f"Executing financial data fetch for ticker: {ticker}")
        try:
            stock = yf.Ticker(ticker)
            info = stock.info
            # Select a subset of useful information
            return {
                "symbol": info.get("symbol"),
                "longName": info.get("longName"),
                "currentPrice": info.get("currentPrice"),
                "previousClose": info.get("previousClose"),
                "open": info.get("open"),
                "dayHigh": info.get("dayHigh"),
                "dayLow": info.get("dayLow"),
                "volume": info.get("volume"),
                "marketCap": info.get("marketCap"),
                "fiftyTwoWeekHigh": info.get("fiftyTwoWeekHigh"),
                "fiftyTwoWeekLow": info.get("fiftyTwoWeekLow"),
                "forwardPE": info.get("forwardPE"),
            }
        except Exception as e:
            logging.error(f"Error fetching financial data for {ticker}: {e}")
            return {"error": f"Could not fetch data for ticker {ticker}. Please ensure it is a valid stock symbol."}

# --- SERVICES ---
class QueryAnalysisService:
    """Service to analyze the user's query and decide on a plan."""
    def __init__(self, tools: List[BaseTool]):
        self.tools = {tool.name: tool for tool in tools}
        self.tool_schemas = self._generate_tool_schemas()

    def _generate_tool_schemas(self) -> List[Dict[str, Any]]:
        schemas = []
        for tool in self.tools.values():
            # This is a simplified schema generation. For more complex tools,
            # you might want to use Pydantic models to generate JSON schemas.
            schema = {
                "type": "function",
                "function": {
                    "name": tool.name,
                    "description": tool.description,
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": "The search query or topic."
                            },
                            "ticker": {
                                "type": "string",
                                "description": "The stock ticker symbol (e.g., 'AAPL')."
                            }
                        },
                        "required": ["query"] if "search" in tool.name else ["ticker"]
                    }
                }
            }
            schemas.append(schema)
        return schemas

    async def get_plan(self, query: str, conversation_history: List[Dict[str, str]]) -> AgentAction:
        logging.info("Generating a plan for the query...")
        system_prompt = "You are an AI agent that decides which tools to use to answer a user's query. You have access to the following tools. Respond with a JSON object containing a list of tool calls."
        
        messages = [
            {"role": "system", "content": system_prompt},
            *conversation_history,
            {"role": "user", "content": query}
        ]

        try:
            response = await groq_client.chat.completions.create(
                model="llama3-70b-8192",
                messages=messages,
                tools=self.tool_schemas,
                tool_choice="auto",
                temperature=0.0
            )

            response_message = response.choices[0].message
            tool_calls_data = response_message.tool_calls

            if tool_calls_data:
                tool_calls = []
                for tc in tool_calls_data:
                    tool_calls.append(ToolCall(
                        name=tc.function.name,
                        parameters=json.loads(tc.function.arguments)
                    ))
                return AgentAction(
                    tool_calls=tool_calls,
                    log=f"Decided to use tools: {[tc.name for tc in tool_calls]}"
                )
            else:
                # If no tool is chosen, the LLM might be able to answer directly
                return AgentAction(tool_calls=[], log="Decided to answer directly.")

        except Exception as e:
            logging.error(f"Error in query analysis: {e}")
            return AgentAction(tool_calls=[], log=f"Error during planning: {e}")

class InformationProcessingService:
    """Service to synthesize information from tool outputs into a coherent response."""

    async def synthesize_response(self, query: str, tool_outputs: Dict[str, Any], conversation_history: List[Dict[str, str]]) -> Dict[str, Any]:
        logging.info("Synthesizing final response...")
        system_prompt = """
You are an AI assistant that synthesizes information from various sources to provide a comprehensive, well-structured, and coherent answer to the user's query.

- Combine the information from the provided tool outputs.
- Use the conversation history for context.
- If the sources provide conflicting information, point that out.
- Provide clear source attribution in your response using markdown links where possible.
- Assess the reliability of your generated answer and provide a confidence score (0-100).
- Remove any redundant information.
- Format your response in Markdown.
"""

        prompt = f"""
User Query: {query}

Tool Outputs: {json.dumps(tool_outputs, indent=2)}

Based on the above information and the conversation history, please generate a response.
"""

        messages = [
            {"role": "system", "content": system_prompt},
            *conversation_history,
            {"role": "user", "content": prompt}
        ]

        try:
            chat_completion = await groq_client.chat.completions.create(
                model="llama3-70b-8192",
                messages=messages,
                temperature=0.7,
            )

            content = chat_completion.choices[0].message.content

            # A simple way to get a confidence score - ask the LLM to include it
            # A more robust method would be to have a separate classification step
            confidence_score_prompt = f"Based on the following response, what is your confidence score (0-100) in its accuracy and completeness?\n\nResponse: {content}\n\nConfidence Score:"
            
            score_completion = await groq_client.chat.completions.create(
                model="llama3-8b-8192",
                messages=[{"role": "user", "content": confidence_score_prompt}],
                temperature=0.0,
            )

            score_text = score_completion.choices[0].message.content
            confidence = int(''.join(filter(str.isdigit, score_text))) if any(char.isdigit() for char in score_text) else 85

            return {
                "content": content,
                "confidence_score": confidence,
                "sources": self._extract_sources(tool_outputs)
            }

        except Exception as e:
            logging.error(f"Error in response synthesis: {e}")
            return {"error": "Failed to synthesize a response."}

    def _extract_sources(self, tool_outputs: Dict[str, Any]) -> List[Dict[str, str]]:
        sources = []
        for tool_name, output in tool_outputs.items():
            if isinstance(output, list):
                for item in output:
                    if isinstance(item, dict) and 'url' in item:
                        sources.append({"name": item.get("title") or item.get("source"), "url": item.get("url")})
            elif isinstance(output, dict) and 'symbol' in output:
                sources.append({"name": f"Yahoo Finance for {output['symbol']}", "url": f"https://finance.yahoo.com/quote/{output['symbol']}"})
        return sources

class MemoryService:
    """Service for managing the agent's memory using ChromaDB."""

    def add_to_memory(self, user_id: str, query: str, response: str):
        logging.info("Adding interaction to memory.")
        try:
            # We can store both the query and response for better context retrieval
            document = f"User query: {query}\nAI response: {response}"
            doc_id = f"{user_id}-{datetime.utcnow().isoformat()}"
            
            memory_collection.add(
                documents=[document],
                metadatas=[{"user_id": user_id, "timestamp": datetime.utcnow().timestamp()}],
                ids=[doc_id]
            )
        except Exception as e:
            logging.error(f"Error adding to memory: {e}")

    def search_memory(self, user_id: str, query: str, n_results: int = 3) -> List[str]:
        logging.info("Searching memory for relevant context.")
        try:
            results = memory_collection.query(
                query_texts=[query],
                n_results=n_results,
                where={"user_id": user_id}
            )
            return results.get('documents', [[]])[0]
        except Exception as e:
            logging.error(f"Error searching memory: {e}")
            return []

# --- CORE AGENT LOGIC ---
class Agent:
    """The main agent that orchestrates the entire process."""
    def __init__(self):
        self.tools = [WebSearchTool(), NewsSearchTool(), FinancialTool()]
        self.analysis_service = QueryAnalysisService(self.tools)
        self.processing_service = InformationProcessingService()
        self.memory_service = MemoryService()
        self.tool_mapping = {tool.name: tool for tool in self.tools}

    async def run(self, user_id: str, query: str, conversation_history: List[Dict[str, str]]):
        start_time = datetime.utcnow()
        
        # Send initial status update
        socketio.emit('status_update', {"message": "Analyzing query..."}, room=user_id)
        
        # Get relevant context from memory
        # memory_context = self.memory_service.search_memory(user_id, query)
        # if memory_context:
        #     socketio.emit('status_update', {"message": f"Found {len(memory_context)} relevant memories."}, room=user_id)

        # 1. Planning
        plan = await self.analysis_service.get_plan(query, conversation_history)
        socketio.emit('status_update', {"message": plan.log}, room=user_id)

        # 2. Tool Execution
        tool_outputs = {}
        if plan.tool_calls:
            socketio.emit('status_update', {"message": "Executing tools..."}, room=user_id)
            tasks = []
            for tool_call in plan.tool_calls:
                if tool_call.name in self.tool_mapping:
                    tool = self.tool_mapping[tool_call.name]
                    tasks.append(tool.execute(**tool_call.parameters))
                else:
                    logging.warning(f"Tool '{tool_call.name}' not found.")

            # Run tools in parallel
            results = await asyncio.gather(*tasks, return_exceptions=True)
            for i, tool_call in enumerate(plan.tool_calls):
                if isinstance(results[i], Exception):
                    tool_outputs[tool_call.name] = {"error": str(results[i])}
                else:
                    tool_outputs[tool_call.name] = results[i]

            socketio.emit('status_update', {"message": "Finished tool execution."}, room=user_id)
            socketio.emit('debug_info', {"title": "Tool Outputs", "content": tool_outputs}, room=user_id)

        # 3. Response Synthesis
        socketio.emit('status_update', {"message": "Synthesizing response..."}, room=user_id)
        final_response_data = await self.processing_service.synthesize_response(query, tool_outputs, conversation_history)

        # 4. Memory Storage
        # Run in the background so it doesn't block the response
        asyncio.create_task(self._add_to_memory_async(user_id, query, final_response_data.get("content", "")))

        # 5. Send final response
        end_time = datetime.utcnow()
        processing_time = (end_time - start_time).total_seconds()

        response_payload = {
            "response": final_response_data.get("content"),
            "confidence": final_response_data.get("confidence_score"),
            "sources": final_response_data.get("sources"),
            "processing_time": round(processing_time, 2),
            "method": "Direct Answer" if not plan.tool_calls else f"Used Tools: {[tc.name for tc in plan.tool_calls]}"
        }

        socketio.emit('final_response', response_payload, room=user_id)
        return response_payload

    async def _add_to_memory_async(self, user_id: str, query: str, response: str):
        # This is a wrapper to make the memory service call awaitable for create_task
        self.memory_service.add_to_memory(user_id, query, response)

# --- FLASK CONNECTION MANAGER ---
class ConnectionManager:
    def __init__(self):
        self.conversations: Dict[str, List[Dict[str, str]]] = {}

    def get_history(self, client_id: str) -> List[Dict[str, str]]:
        return self.conversations.get(client_id, [])

    def add_to_history(self, client_id: str, user_message: str, ai_response: str):
        if client_id not in self.conversations:
            self.conversations[client_id] = []
        self.conversations[client_id].append({"role": "user", "content": user_message})
        self.conversations[client_id].append({"role": "assistant", "content": ai_response})

    def clear_history(self, client_id: str):
        if client_id in self.conversations:
            del self.conversations[client_id]

manager = ConnectionManager()
agent = Agent()

# --- FLASK ROUTES ---
@app.route("/")
def index():
    return render_template('index.html')

@app.route("/health")
def health():
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0.0"
    })

# --- SOCKETIO EVENTS ---
@socketio.on('connect')
def handle_connect():
    client_id = request.sid
    logging.info(f"Client {client_id} connected.")
    emit('connected', {"client_id": client_id, "message": "Connected to Agentic AI"})

@socketio.on('disconnect')
def handle_disconnect():
    client_id = request.sid
    logging.info(f"Client {client_id} disconnected.")

@socketio.on('send_message')
def handle_message(data):
    client_id = request.sid
    user_message = data.get('message', '').strip()
    
    if not user_message:
        emit('error', {"message": "Empty message received."})
        return
    
    logging.info(f"Received message from {client_id}: {user_message}")
    
    # Get conversation history
    conversation_history = manager.get_history(client_id)
    
    # Run the agent in a separate thread to handle async operations
    def run_agent():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            result = loop.run_until_complete(agent.run(client_id, user_message, conversation_history))
            # Add to conversation history
            manager.add_to_history(client_id, user_message, result.get("response", ""))
        except Exception as e:
            logging.error(f"Error processing message: {e}")
            socketio.emit('error', {"message": f"Error processing your request: {str(e)}"}, room=client_id)
        finally:
            loop.close()
    
    # Start the agent in a background thread
    thread = threading.Thread(target=run_agent)
    thread.daemon = True
    thread.start()

@socketio.on('clear_history')
def handle_clear_history():
    client_id = request.sid
    manager.clear_history(client_id)
    emit('history_cleared', {"message": "Conversation history cleared."})
    logging.info(f"Cleared conversation history for client {client_id}")

@socketio.on('get_history')
def handle_get_history():
    client_id = request.sid
    history = manager.get_history(client_id)
    emit('conversation_history', {"history": history})

# --- RUN THE APP ---
if __name__ == '__main__':
    print("=" * 60)
    print("🚀 Starting Agentic AI Flask Server...")
    print("=" * 60)
    print("📍 Server running at: http://localhost:5000")
    print("🔗 WebSocket endpoint: ws://localhost:5000/socket.io/")
    print("💡 Features available:")
    print("   - Web Search (DuckDuckGo)")
    print("   - News Search")
    print("   - Financial Data (Yahoo Finance)")
    print("   - Conversation Memory (ChromaDB)")
    print("=" * 60)
    
    # Run with SocketIO
    socketio.run(
        app, 
        host='0.0.0.0', 
        port=5000, 
        debug=True, 
        allow_unsafe_werkzeug=True
    )
