FROM python:3.12-slim

WORKDIR /core

COPY pyproject.toml requirements.txt ./

RUN pip install --no-cache-dir -r requirements.txt

COPY runtime ./runtime

RUN pip install --no-cache-dir .

CMD ["python", "-c", "import runtime; print('Base image loaded')"]
