FROM python:3.10-alpine

WORKDIR /code

COPY requirements.txt .

RUN apk add --no-cache gcc musl-dev linux-headers

RUN pip install -r requirements.txt

COPY tanglenomicon_data_api/ tanglenomicon_data_api/

EXPOSE 8000

ENV PORT 8000

CMD [ "python", "-m", "tanglenomicon_data_api","run", "--cfg", "/data/config.yaml" ]