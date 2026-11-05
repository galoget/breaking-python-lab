FROM python:3.12-slim

# ping is required for the command injection challenge
RUN apt-get update \
    && apt-get install -y --no-install-recommends iputils-ping \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt

COPY app/ /app/
COPY start.sh /start.sh

RUN useradd --create-home lab && chown -R lab:lab /app
USER lab

EXPOSE 5000

# The app binds to $HOST inside the container. 0.0.0.0 is required so the port
# published by Docker reaches it; exposure is still limited by docker-compose.yml,
# which publishes the port only to 127.0.0.1 on the host.
ENV HOST=0.0.0.0

CMD ["/bin/sh", "/start.sh"]
