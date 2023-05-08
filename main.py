from fastapi import FastAPI
from database import connection
from routes.auth import auth_router
from routes.messages import messages_router

app = FastAPI()

app.include_router(auth_router, prefix="/auth")
app.include_router(messages_router, prefix="/messages")


@app.on_event("startup")
def init_db():
    connection.conn()
    connection.populate_database()


@app.get("/")
async def root() -> dict:
    return {"message": "success!"}
