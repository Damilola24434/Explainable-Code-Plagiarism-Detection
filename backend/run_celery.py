#!/usr/bin/env python
"""Simple script to start Celery worker with proper module imports."""

import sys
import os

# Add backend directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.celery import celery_app

if __name__ == "__main__":
    celery_app.worker_main(argv=["worker", "--loglevel=info"])
