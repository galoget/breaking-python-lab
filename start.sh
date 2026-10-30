#!/bin/sh
# Simulated internal service (127.0.0.1 only) + the lab application.
python internal_service.py &
exec python app.py
