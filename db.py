from motor.motor_asyncio import AsyncIOMotorClient

class DataBase:
    client: AsyncIOMotorClient = None

db = DataBase()

def get_database() -> DataBase:
    return db

async def connect_to_mongo():
    db.client = AsyncIOMotorClient("mongodb+srv://admin:admin@cluster0.ouwdlq3.mongodb.net/?retryWrites=true&w=majority")
    db.mongodb = db.client["Cluster0"]

async def close_mongo_connection():
    db.client.close()