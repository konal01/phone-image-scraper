FROM mcr.microsoft.com/playwright/python:v1.40.0-jammy

WORKDIR /app

# Upgrade pip and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY . .

# Ensure build script is executable
RUN chmod +x ./build.sh || true

ENV PORT=8000
EXPOSE 8000

# Start FastAPI server on dynamic Render PORT
CMD ["sh", "-c", "uvicorn app:app --host 0.0.0.0 --port ${PORT:-8000}"]
