FROM python:3.12-slim

WORKDIR /core

COPY pyproject.toml requirements.txt ./

RUN pip install --no-cache-dir -r requirements.txt

COPY input_pool ./input_pool

RUN pip install --no-cache-dir .

CMD ["input-pool"]
