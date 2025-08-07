# Stage 1: Use an official Python runtime as a parent image
FROM python:3.9-slim

# Set the working directory inside the container
WORKDIR /app

# Copy the requirements file first to leverage Docker's build cache
COPY ./frontend/requirements.txt .

# Install the Python dependencies from the requirements file
RUN pip install --no-cache-dir -r requirements.txt

# Now copy the application code
COPY ./frontend/app.py .

# Expose the port that Streamlit runs on by default (and that Cloud Run will use)
EXPOSE 8080

# Define the health check for Cloud Run to know the app is ready
HEALTHCHECK CMD streamlit hello

# Define the command to run your Streamlit app
CMD ["sh", "-c", "streamlit run app.py --server.port=$PORT --server.enableCORS=false"]
