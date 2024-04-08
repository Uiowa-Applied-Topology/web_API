from fastapi import Depends, FastAPI

# from .internal import admin
from .montesinos import endpoint as mont_e
from .internal import db_connector, security, config
import uvicorn
from fastapi import FastAPI
import argparse

app: FastAPI = FastAPI()


app.include_router(security.router)
app.include_router(mont_e.router)


@app.get("/")
async def root():
    return {"message": "Hello Bigger Applications!"}


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-c", "--cfg")
    args = parser.parse_args()
    settings = config.Settings()
    settings.load(args.cfg)
    db_cfg = settings.yaml_settings["db-connection"]
    db_connector = db_connector.load(
        db_cfg["domain"],
        db_cfg["port"],
        db_cfg["user"],
        db_cfg["password"],
        db_cfg["database"],
    )
    # run server
    uvicorn.run(app)
