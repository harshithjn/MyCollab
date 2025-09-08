from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import json
import uuid
from typing import Dict, List, Set
import asyncio
from datetime import datetime
import uvicorn
import os

from operational_transform import OperationalTransform
from document_manager import DocumentManager

app = FastAPI(title="MyCollab - Collaborative Code Editor")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

doc_manager = DocumentManager()
ot = OperationalTransform()

class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, Set[WebSocket]] = {}
        self.user_info: Dict[WebSocket, dict] = {}

    async def connect(self, websocket: WebSocket, doc_id: str, user_id: str, username: str):
        await websocket.accept()
        
        if doc_id not in self.active_connections:
            self.active_connections[doc_id] = set()
        
        self.active_connections[doc_id].add(websocket)
        self.user_info[websocket] = {
            "user_id": user_id,
            "username": username,
            "doc_id": doc_id,
            "cursor_position": {"line": 0, "column": 0}
        }
        
        doc_state = doc_manager.get_document(doc_id)
        if not doc_state:
            doc_manager.create_document(doc_id)
            doc_state = doc_manager.get_document(doc_id)
        
        await websocket.send_text(json.dumps({
            "type": "document_state",
            "content": doc_state["content"],
            "version": doc_state["version"]
        }))
        
        await self.broadcast_user_joined(doc_id, user_id, username, websocket)

    def disconnect(self, websocket: WebSocket):
        if websocket in self.user_info:
            user_info = self.user_info[websocket]
            doc_id = user_info["doc_id"]
            user_id = user_info["user_id"]
            username = user_info["username"]
            
            if doc_id in self.active_connections:
                self.active_connections[doc_id].discard(websocket)
                if not self.active_connections[doc_id]:
                    del self.active_connections[doc_id]
            
            del self.user_info[websocket]
            
            asyncio.create_task(self.broadcast_user_left(doc_id, user_id, username))

    async def broadcast_user_joined(self, doc_id: str, user_id: str, username: str, exclude_websocket: WebSocket):
        if doc_id in self.active_connections:
            message = json.dumps({
                "type": "user_joined",
                "user_id": user_id,
                "username": username
            })
            for connection in self.active_connections[doc_id]:
                if connection != exclude_websocket:
                    try:
                        await connection.send_text(message)
                    except:
                        pass

    async def broadcast_user_left(self, doc_id: str, user_id: str, username: str):
        if doc_id in self.active_connections:
            message = json.dumps({
                "type": "user_left",
                "user_id": user_id,
                "username": username
            })
            for connection in self.active_connections[doc_id]:
                try:
                    await connection.send_text(message)
                except:
                    pass

    async def broadcast_to_document(self, doc_id: str, message: dict, exclude_websocket: WebSocket = None):
        if doc_id in self.active_connections:
            message_str = json.dumps(message)
            for connection in self.active_connections[doc_id]:
                if connection != exclude_websocket:
                    try:
                        await connection.send_text(message_str)
                    except:
                        pass

    async def broadcast_cursor_update(self, doc_id: str, user_id: str, cursor_position: dict, exclude_websocket: WebSocket = None):
        if doc_id in self.active_connections:
            message = json.dumps({
                "type": "cursor_update",
                "user_id": user_id,
                "cursor_position": cursor_position
            })
            for connection in self.active_connections[doc_id]:
                if connection != exclude_websocket:
                    try:
                        await connection.send_text(message)
                    except:
                        pass

manager = ConnectionManager()

@app.get("/")
async def read_root():
    return FileResponse("../frontend/index.html")

@app.get("/api/documents/{doc_id}")
async def get_document(doc_id: str):
    doc = doc_manager.get_document(doc_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    return doc

@app.post("/api/documents")
async def create_document():
    doc_id = str(uuid.uuid4())
    doc_manager.create_document(doc_id)
    return {"doc_id": doc_id, "message": "Document created successfully"}

@app.websocket("/ws/{doc_id}")
async def websocket_endpoint(websocket: WebSocket, doc_id: str):
    user_id = websocket.query_params.get("user_id", str(uuid.uuid4()))
    username = websocket.query_params.get("username", f"User_{user_id[:8]}")
    
    await manager.connect(websocket, doc_id, user_id, username)
    
    try:
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)
            
            if message["type"] == "operation":
                operation = message["operation"]
                client_version = message["version"]
                
                doc_state = doc_manager.get_document(doc_id)
                if not doc_state:
                    await websocket.send_text(json.dumps({
                        "type": "error",
                        "message": "Document not found"
                    }))
                    continue
                
                transformed_ops = ot.transform_operation(
                    operation, 
                    doc_state["operations"][client_version:],
                    doc_state["version"]
                )
                
                new_content = ot.apply_operation(doc_state["content"], transformed_ops)
                new_version = doc_manager.apply_operation(doc_id, transformed_ops, new_content)
                
                await manager.broadcast_to_document(doc_id, {
                    "type": "operation_applied",
                    "operation": transformed_ops,
                    "version": new_version,
                    "user_id": user_id
                }, exclude_websocket=websocket)
                
                await websocket.send_text(json.dumps({
                    "type": "operation_confirmed",
                    "version": new_version
                }))
                
            elif message["type"] == "cursor_update":
                cursor_position = message["cursor_position"]
                if websocket in manager.user_info:
                    manager.user_info[websocket]["cursor_position"] = cursor_position
                
                await manager.broadcast_cursor_update(
                    doc_id, user_id, cursor_position, exclude_websocket=websocket
                )
                
            elif message["type"] == "content_update":
                new_content = message["content"]
                new_version = doc_manager.update_document(doc_id, new_content)
                
                await manager.broadcast_to_document(doc_id, {
                    "type": "content_update",
                    "content": new_content,
                    "version": new_version,
                    "user_id": user_id
                }, exclude_websocket=websocket)
                
            elif message["type"] == "chat_message":
                await manager.broadcast_to_document(doc_id, {
                    "type": "chat_message",
                    "message": message["message"],
                    "username": message["username"]
                })
                
    except WebSocketDisconnect:
        manager.disconnect(websocket)

app.mount("/static", StaticFiles(directory="../frontend/static"), name="static")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)