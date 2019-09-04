# Use the Python3.7.2 image
FROM python:3.7.2-stretch

# Set the working directory to /app
WORKDIR /app

# Copy the current directory contents into the container at /app
ADD . /app

# Install the dependencies
RUN pip install -r requirements.txt

# Download the language model
RUN python -m spacy download en_core_web_md

# run the command to start uWSGI
# CMD ["uwsgi", "app.ini"]