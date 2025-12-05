from app import create_app

app, socketio = create_app()

if __name__ == "__main__":
    print("🚀 Starting Enhanced Agentic AI Server...")
    print("📱 Access the interface at http://localhost:5000")
    socketio.run(app, debug=True, use_reloader=False, port=5000)
