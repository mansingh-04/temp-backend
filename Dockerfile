FROM python:3.9-slim

WORKDIR /app

# Copy only requirements and installation scripts first
COPY requirements.txt install.sh ./
RUN chmod +x install.sh

# Run installation script
RUN ./install.sh

# Copy the rest of the application
COPY . .

# Make start script executable
RUN chmod +x start.sh

# Set environment variables
ENV PORT=5050
ENV PYTHONUNBUFFERED=1

# Run the application
CMD ["bash", "start.sh"] 