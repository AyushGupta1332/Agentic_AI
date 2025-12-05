from typing import Dict, List

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
