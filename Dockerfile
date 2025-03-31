FROM python:3.9-slim

# Install system dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    git \
    gcc \
    g++ \
    libgl1 \
    libglib2.0-0 && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

# First copy requirements to cache dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Manually install AnimeGANv2
RUN git clone https://github.com/TachibanaYoshino/AnimeGANv2.git && \
    cp -r AnimeGANv2/AnimeGANv2 ./AnimeGANv2 && \
    rm -rf AnimeGANv2

# Copy the rest of the application
COPY . .

CMD ["python", "main.py"]
