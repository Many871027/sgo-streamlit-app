# Stage 1: Use an official Python runtime as a parent image
FROM python:3.9-slim

# Set the working directory inside the container
WORKDIR /app

# Copy the contents of the backend/app directory directly into the container's WORKDIR.
COPY ./backend/app .

# Also copy the requirements file into the WORKDIR.
COPY ./backend/requirements.txt .

# Install the Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Expose the port that Cloud Run will use
EXPOSE 8080

# Define the final, robust command to run your app.
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]
