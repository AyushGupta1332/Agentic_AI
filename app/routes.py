import asyncio
import logging
from datetime import datetime
from flask import render_template, jsonify, request
from app.agents.enhanced_agent import EnhancedAgent
from app.connection import ConnectionManager

# Initialize global instances
agent = EnhancedAgent()
manager = ConnectionManager()

def init_routes(app, socketio):
    
    @app.route("/")
    def index():
        return render_template('index.html')

    @app.route("/health")
    def health():
        return jsonify({
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "version": "2.0.0",
            "features": [
                "Enhanced Web Search with Language Filtering",
                "Social Media Search Tool", 
                "Enhanced News Search",
                "Improved Financial Data",
                "Better Error Handling",
                "Casual Conversation Detection"
            ]
        })

    # --- SOCKETIO EVENTS ---

    @socketio.on('connect')
    def handle_connect():
        client_id = request.sid
        logging.info(f"Client {client_id} connected.")
        socketio.emit('connected', {"client_id": client_id, "message": "Connected to Enhanced Agentic AI"}, room=client_id)

    @socketio.on('disconnect')
    def handle_disconnect():
        client_id = request.sid
        logging.info(f"Client {client_id} disconnected.")
        manager.clear_history(client_id)

    @socketio.on('clear_history')
    def handle_clear_history():
        client_id = request.sid
        logging.info(f"Client {client_id} requested to clear history.")
        manager.clear_history(client_id)
        socketio.emit('history_cleared', {"message": "Conversation history cleared"}, room=client_id)

    @socketio.on('send_message')
    def handle_message(data):
        client_id = request.sid
        user_message = data.get('message')
        
        if not user_message:
            return

        logging.info(f"Received message from {client_id}: {user_message}")
        
        # Get conversation history
        history = manager.get_history(client_id)
        
        # Wrapper to run async agent in a background thread
        def run_agent_wrapper(uid, msg, hist, sio):
            response_payload = asyncio.run(agent.run(uid, msg, hist, sio))
            
            # Update history in ConnectionManager
            if response_payload:
                ai_response = response_payload.get("response", "")
                manager.add_to_history(uid, msg, ai_response)

        # Process asynchronously
        socketio.start_background_task(
            run_agent_wrapper, 
            client_id, 
            user_message, 
            history,
            socketio
        )
