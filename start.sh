#!/bin/bash
cd backend
gunicorn app:app --bind 0.0.0.0:${PORT:-5050} --log-level debug 