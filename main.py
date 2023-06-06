from fastapi import FastAPI, Depends, WebSocket, WebSocketDisconnect, HTTPException
from database import connection
from routes.auth import auth_router
from routes.messages import messages_router
from routes.users import friends_router
from models import User
from auth.authenticate import authenticate, get_current_user
from auth.jwt_handler import verify_access_token
from database.connection import get_session
from utils.websocket_manager import ConnectionManager
import json

app = FastAPI()

app.include_router(auth_router, prefix="/auth")
app.include_router(messages_router, prefix="/messages")
app.include_router(friends_router, prefix="/friends")


@app.on_event("startup")
def init_db():
    connection.conn()
    connection.populate_database()


@app.get("/")
async def is_logged_in(user: User = Depends(authenticate)) -> dict:
    return {"username": user.username, "email": user.email}


manager = ConnectionManager()


@app.websocket("/ws/{token}")
async def exchange_messages(websocket: WebSocket, token: str, session=Depends(get_session)):
    try:
        decoded_token = verify_access_token(token)
    except HTTPException:
        await websocket.accept()
        await websocket.send_text("TOKEN ERROR")

    user = get_current_user(decoded_token["user"])
    await manager.connect(websocket, user.username)

    try:
        while True:
            message = await websocket.receive_text()
            message = json.loads(message)
            message["sender_username"] = user.username
            await manager.save_encrypted_message(message)
    except WebSocketDisconnect as e:
        manager.disconnect(user.username)
    except RuntimeError as e:
        print("Something went wrong")
