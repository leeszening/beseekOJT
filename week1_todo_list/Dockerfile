# Use official Python image
FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Copy requirements first (for better caching)
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the app
COPY . .

# Expose the port Gunicorn will run on
EXPOSE 8080

# Command to run the app with Gunicorn
CMD ["gunicorn", "--bind", "0.0.0.0:8080", "main:server"]
