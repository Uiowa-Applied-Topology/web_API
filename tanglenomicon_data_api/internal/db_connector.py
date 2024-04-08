from pydantic import ConfigDict, BaseModel, Field, EmailStr
from pydantic.functional_validators import BeforeValidator

from typing_extensions import Annotated, Unpack, Optional

from bson import ObjectId
import motor.motor_asyncio
import urllib.parse
from pymongo import ReturnDocument

client: motor.motor_asyncio = None

db: dict[str, motor.motor_asyncio.AsyncIOMotorDatabase] = None

def init_client(
    url: str,
    port: int,
    username: str,
    password: str,
    database_name: str
):
    global client
    global db
    if client == None:
        if url and port and username and password:
            username = urllib.parse.quote_plus(username)
            password = urllib.parse.quote_plus(password)
            client = motor.motor_asyncio.AsyncIOMotorClient(
                f"mongodb://{username}:{password}@{url}:{port}/?authSource=admin&retryWrites=true&w=majority"
            )
            db = motor.motor_asyncio.AsyncIOMotorDatabase(client, database_name)
        else:
            raise NameError(
                "db connection error"
            )  # @@@FIXME needs to be updated to exception object
    ...


