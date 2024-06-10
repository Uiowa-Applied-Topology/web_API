FROM python:3.10-alpine

WORKDIR /code

COPY requirements.txt .

RUN pip install -r requirements.txt

COPY tanglenomicon_data_api/ tanglenomicon_data_api/

EXPOSE 8000

CMD [ "python", "-m", "/code/tanglenomicon_data_api","run", "--cfg", "/code/config.yaml" ]