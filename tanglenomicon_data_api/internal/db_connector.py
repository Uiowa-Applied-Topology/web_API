"""_summary_

Raises
------
NameError
    _description_
"""

import motor.motor_asyncio
import urllib.parse

client: motor.motor_asyncio = None

db: dict[str, motor.motor_asyncio.AsyncIOMotorDatabase] = None


def init_client(url: str, port: int, username: str, password: str, database_name: str):
    """_summary_

    Parameters
    ----------
    url : str
        _description_
    port : int
        _description_
    username : str
        _description_
    password : str
        _description_
    database_name : str
        _description_

    Raises
    ------
    NameError
        _description_
    """
    global client
    global db
    if url and port and username and password:
        username = urllib.parse.quote_plus(username)
        password = urllib.parse.quote_plus(password)
        client = motor.motor_asyncio.AsyncIOMotorClient(
            f"mongodb://{username}:{password}@{url}:{port}/?authSource=admin&retryWrites=true&w=majority"  # noqa: E501
        )
        db = motor.motor_asyncio.AsyncIOMotorDatabase(client, database_name)
    else:
        raise NameError(
            "db connection error"
        )  # @@@FIXME needs to be updated to exception object
    ...
