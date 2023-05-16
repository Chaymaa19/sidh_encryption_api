from fastapi import FastAPI, Depends
from database import connection
from routes.auth import auth_router
from routes.messages import messages_router
from routes.users import friends_router
from models import User
from auth.authenticate import authenticate

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
    return {"message": "user logged in"}
