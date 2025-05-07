FROM python:3.9-slim

WORKDIR /app

# Copy only requirements and installation scripts first
COPY requirements.txt install.sh ./
RUN chmod +x install.sh

# Run installation script
RUN ./install.sh

# Copy the rest of the application
COPY . .

# Make scripts executable
RUN chmod +x start.sh entrypoint.py

# Set environment variables
ENV PORT=5050
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV FLASK_ENV=production
ENV FLASK_DEBUG=0

# Run the application with our debugging entrypoint
CMD ["python", "entrypoint.py"] 