# Dockerfile for Spotify Soul application
# This Dockerfile sets up a Python environment with the necessary dependencies
# and runs the application server.
# Ensure you have a requirements.txt file with the necessary Python packages.
# The application will run on port 8889.
# To build the Docker image, run:
# docker build -t spotify-soul .
# To run the Docker container, use:
# docker run -p 8889:8889 spotify-soul 
FROM python:3.9-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
EXPOSE 8889
CMD ["gunicorn", "server:app"]
