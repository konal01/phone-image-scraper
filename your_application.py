# Fallback entrypoint in case Render's default placeholder 'your_application' is used
from app import app, root, health_check

__all__ = ["app", "root", "health_check"]
