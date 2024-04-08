from fastapi import Depends, APIRouter, HTTPException, status
from ..internal.security import get_current_active_user, User
from ..internal import db_connector
from datetime import datetime, timedelta, timezone
from typing import Annotated, Union

import motor.motor_asyncio

router = APIRouter()

def get_collection():
    return db_connector.db.get_collection("montesinos")


@router.post("/test")
async def read_users_me(
    collection: Annotated[motor.motor_asyncio.AsyncIOMotorCollection, Depends(get_collection)]
    # current_user: Annotated[User, Depends(get_current_active_user)]
):
    if db_connector.client == None:
        raise HTTPException(status_code=500, detail="Server Error")
    else:
        if (
            student := await collection.find_one()
        ) is not None:
            return student["me"]

    raise HTTPException(status_code=404, detail=f"Student {id} not found")
