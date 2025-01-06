FROM python:3.9-windowsservercore

# Install requirements
COPY requirements.txt .
RUN pip install -r requirements.txt
RUN pip install pyinstaller

# Copy your application
WORKDIR /app
COPY . /app

# Create the executable
CMD pyinstaller --add-data ".env:." --onefile --name="PyInies" --icon=./inies_logo.png ./pyinies/script.py
