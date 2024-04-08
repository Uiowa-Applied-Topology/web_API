from pydantic import ConfigDict, BaseModel, Field, EmailStr
from pydantic.functional_validators import BeforeValidator

from typing_extensions import Annotated, Unpack

from bson import ObjectId
import motor.motor_asyncio
import urllib.parse
from pymongo import ReturnDocument

client: motor.motor_asyncio = None
db: motor.motor_asyncio.AsyncIOMotorDatabase = None


def load(url: str, port: int, username: str, password: str, database: str):
    global client
    global db
    username = urllib.parse.quote_plus(username)
    password = urllib.parse.quote_plus(password)
    client = motor.motor_asyncio.AsyncIOMotorClient(
        f"mongodb://{username}:{password}@{url}:{port}/?authSource=admin&retryWrites=true&w=majority"
    )
    db = motor.motor_asyncio.AsyncIOMotorDatabase(client, database)
    ...
