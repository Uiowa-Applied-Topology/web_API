from datetime import datetime, timedelta, timezone
from typing import Annotated, Union

from fastapi import Depends, APIRouter, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel
import motor.motor_asyncio
from . import db_connector as dbc
from . import config

COL_NAME = "auth"


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    username: Union[str, None] = None


class User(BaseModel):
    username: str
    disabled: Union[bool, None] = None


class UserInDB(User):
    hashed_password: str
    token_expire: int


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

router = APIRouter()


def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password):
    return pwd_context.hash(password)


async def get_user(collection, username: str):
    if (student := await collection.find_one({"username":username})) is not None:
            return UserInDB(**student)


async def authenticate_user(fake_db, username: str, password: str):
    user = await get_user(fake_db, username)
    if not user:
        return False
    if not verify_password(password, user.hashed_password):
        return False
    return user


def get_collection():
    return dbc.db[COL_NAME]


def create_access_token(data: dict, expires_delta: Union[timedelta, None] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, config.config["auth"]["secret_key"], algorithm=config.config["auth"]["algorithm"])
    return encoded_jwt


async def auth_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    collection: Annotated[
        motor.motor_asyncio.AsyncIOMotorCollection, Depends(get_collection)
    ],
):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, config.config["auth"]["secret_key"], algorithms=[config.config["auth"]["algorithm"]])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username)
    except JWTError:
        raise credentials_exception
    return True

async def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    collection: Annotated[
        motor.motor_asyncio.AsyncIOMotorCollection, Depends(get_collection)
    ],
):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, config.config["auth"]["secret_key"], algorithms=[config.config["auth"]["algorithm"]])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username)
    except JWTError:
        raise credentials_exception
    user = await get_user(collection, username=token_data.username)
    if user is None:
        raise credentials_exception
    return user


async def get_current_active_user(
    current_user: Annotated[User, Depends(get_current_user)]
):
    if current_user.disabled:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user


@router.get("/users/me/", response_model=User)
async def read_users_me(
    current_user: Annotated[User, Depends(get_current_active_user)]
):
    return current_user


@router.post("/token")
async def login_for_access_token(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    collection: Annotated[
        motor.motor_asyncio.AsyncIOMotorCollection, Depends(get_collection)
    ],
) -> Token:
    user = await authenticate_user(collection, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=user.token_expire)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return Token(access_token=access_token, token_type="bearer")
