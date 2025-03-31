FROM python:3.9-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    libgl1 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Clone and install AnimeGANv2
RUN git clone https://github.com/TachibanaYoshino/AnimeGANv2.git && \
    cd AnimeGANv2 && pip install -r requirements.txt

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["python", "main.py"]
