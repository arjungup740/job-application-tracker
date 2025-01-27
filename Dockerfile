# Use an official Python runtime as a parent image
FROM python:3.12-slim

# Set the working directory in the container
WORKDIR /app

# Copy the requirements file into the container
COPY requirements.txt .

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code
COPY . .

# Copy service account credentials file -- this is redundant just making explicit what's happenning
# COPY email-jobs-manager-service-account-creds.json .

# Set environment variables
ENV PYTHONUNBUFFERED=1

# Run the script when the container launches
CMD ["python", "v2.py"]
