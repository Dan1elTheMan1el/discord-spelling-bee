# Use official Python image
FROM python:3.11

# Set working directory
WORKDIR /app

# Copy requirements and install
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the app
COPY . .

# Run the bot
CMD ["python", "discord-spelling-bee.py"]