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

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install --no-cache-dir torch==1.12.1+cu113 -f https://download.pytorch.org/whl/torch_stable.html

# Manually install AnimeGANv2
RUN git clone https://github.com/TachibanaYoshino/AnimeGANv2.git && \
    mkdir -p AnimeGANv2 && \
    cp -r AnimeGANv2/AnimeGANv2/* ./AnimeGANv2/ && \
    rm -rf AnimeGANv2

# Copy application files
COPY . .

CMD ["python", "main.py"]
