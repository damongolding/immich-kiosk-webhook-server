FROM --platform=$BUILDPLATFORM python:slim

RUN pip install uv

WORKDIR /app
COPY requirements.lock ./
RUN uv pip install --no-cache --system -r requirements.lock

COPY src/kiosk_webhooks ./

CMD ["python", "app.py"]
