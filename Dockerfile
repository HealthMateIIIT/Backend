# Use official Python runtime as a parent image
FROM python:3.12-slim

# Do not write pyc files and ensure output is sent straight to terminal
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Set working directory
WORKDIR /app

# Install system dependencies (small and common ones)
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
       build-essential \
       gcc \
       libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy only requirements first to leverage Docker layer caching
COPY requirements.txt ./

# Upgrade pip and install Python dependencies (include gunicorn for production)
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt gunicorn

# Copy application source
COPY . .

# Create a non-root user and take ownership of the app directory
RUN groupadd -r appgroup \
    && useradd -r -g appgroup appuser \
    && chown -R appuser:appgroup /app

USER appuser

# Expose the port the app runs on (Flask default is 5000)
EXPOSE 5000

ENV GEMINI_API="AIzaSyDNHndi3AYzaIPVhUlqno5ZzG68HfL7CXo"

# Default command: run with gunicorn. Adjust MODULE if your app object is elsewhere.
# Expectation: `server.py` defines `app = Flask(__name__)` so gunicorn can import `server:app`.
CMD ["gunicorn", "server:app", "--bind", "0.0.0.0:5000", "--workers", "4", "--threads", "4"]
