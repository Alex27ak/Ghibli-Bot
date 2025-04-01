FROM python:3.9-slim

WORKDIR /app

# Install System Dependencies
RUN apt-get update && apt-get install -y \
    libgl1 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Copy Dependencies
COPY requirements.txt . 
RUN pip install --no-cache-dir -r requirements.txt

# Copy Model and Code
COPY . .

CMD ["python", "main.py"]
