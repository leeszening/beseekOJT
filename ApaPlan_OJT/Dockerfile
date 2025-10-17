# Use an official Python runtime as a parent image
FROM python:3.9-slim

# Set the working directory in the container
WORKDIR /app

# Upgrade pip
RUN pip install --upgrade pip

# Copy the dependencies file to the working directory
COPY requirement.txt .

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirement.txt

# Copy the rest of the application code
COPY src/ .
COPY firebase_config.py .

# Create a non-root user and switch to it
RUN useradd --create-home appuser
USER appuser

# Tell Cloud Run which port the app is listening on
EXPOSE 8080

# Run app.py when the container launches, using the PORT variable
CMD ["python", "main.py"]
