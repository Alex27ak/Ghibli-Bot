# Stage 1: Builder to install dependencies
FROM python:3.9-alpine AS builder

WORKDIR /app

# Install necessary system dependencies
RUN apk add --no-cache libjpeg-turbo-dev zlib-dev gcc musl-dev

# Copy and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Stage 2: Final lightweight image
FROM python:3.9-alpine

WORKDIR /app

# Copy installed dependencies from the builder stage
COPY --from=builder /usr/local /usr/local
COPY . .

CMD ["python", "main.py"]
