FROM python:3.11-slim

# Set workdir
WORKDIR /app

# Install system dependencies for builds (if needed)
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the code
COPY . .

# Install the package in editable mode (if pyproject.toml/setup.py present)
RUN pip install -e .

# Set environment variables (override in deployment)
ENV PYTHONUNBUFFERED=1

# Default command (can be overridden)
CMD ["python", "-m", "prediction_logger.cli", "--verbose"]
