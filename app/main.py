from fastapi import FastAPI
from .db import connect_to_mongo, close_mongo_connection
from .routes import router

app = FastAPI()

app.add_event_handler("startup", connect_to_mongo)
app.add_event_handler("shutdown", close_mongo_connection)

app.include_router(router)

@app.get("/")
def read_root():
    return {"message": "Hello, World!"}

app.add_event_handler("startup", connect_to_mongo)
app.add_event_handler("shutdown", close_mongo_connection)

app.include_router(router)