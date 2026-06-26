# Use Python 3.10 slim image
FROM python:3.10-slim

# Install Node.js (needed to build React frontend)
RUN apt-get update && apt-get install -y \
    curl \
    gnupg \
    libgl1-mesa-glx \
    libglib2.0-0 \
    && curl -fsSL https://deb.nodesource.com/setup_18.x | bash - \
    && apt-get install -y nodejs \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirement files first to cache Docker layers
COPY requirements.txt .

# Install Python dependencies
# Adding --no-cache-dir to save space
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application
COPY . .

# Build the React frontend
RUN cd frontend && npm install && npm run build

# Expose the port Hugging Face Spaces uses
EXPOSE 7860

# Command to run the Flask app using Gunicorn on port 7860
CMD ["gunicorn", "-b", "0.0.0.0:7860", "--timeout", "120", "app:app"]
