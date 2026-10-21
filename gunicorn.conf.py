import os

# Automatically bind to Render's dynamic port
bind = f"0.0.0.0:{os.environ.get('PORT', '8000')}"

# Use Uvicorn worker class so FastAPI ASGI runs seamlessly on Gunicorn
worker_class = "uvicorn.workers.UvicornWorker"

# Use 1 worker to conserve RAM on Free tier (512MB)
workers = 1

# Allow generous timeout for scraping operations
timeout = 180
keepalive = 5
