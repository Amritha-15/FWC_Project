import json
from typing import List
from fastapi import WebSocket

class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        print(f"✅ Admin WebSocket connected. Total connections: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
            print(f"❌ Admin WebSocket disconnected. Remaining connections: {len(self.active_connections)}")

    async def send_personal_message(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)

    async def broadcast(self, event_type: str, data: dict):
        """
        Broadcasts structured events (NEW_APPLICATION, CANDIDATE_SHORTLISTED, etc.) to all connected admin clients.
        """
        message = json.dumps({
            "event_type": event_type,
            "data": data
        })
        
        inactive_connections = []
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except Exception as e:
                print(f"Failed to send websocket broadcast to connection: {e}")
                inactive_connections.append(connection)
                
        # Clean up any failed connections
        for conn in inactive_connections:
            self.disconnect(conn)

# Singleton manager
ws_manager = ConnectionManager()
