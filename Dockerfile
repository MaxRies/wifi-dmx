FROM pysergio/pypoetry:3.10-alpine

WORKDIR /app

COPY pyproject.toml /app/pyproject.toml
COPY poetry.lock /app/poetry.lock

RUN poetry install

COPY . .

CMD [ "python", "./wifidmx/controller.py" ]