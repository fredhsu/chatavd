FROM python:3.11

EXPOSE 8080

RUN pip install poetry==1.4.2

ENV POETRY_CACHE_DIR=/tmp/poetry \
    POETRY_NO_INTERACTION=true

WORKDIR /app/

COPY pyproject.toml poetry.lock main.py avdrag.py ./

RUN touch README.md

RUN poetry install --without dev --no-root && rm -rf $POETRY_CACHE_DIR

COPY main.py avdrag.py ./

RUN poetry install --without dev

ENTRYPOINT ["poetry", "run", "python", "-m", "main"]

