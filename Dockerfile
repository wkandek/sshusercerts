# Use an official Python runtime as a parent image
FROM ubuntu:18.04

# Set the working directory to /app
WORKDIR /app

# Copy the current directory contents into the container at /app
COPY . /app

# Install any needed packages specified in requirements.txt
# RUN pip install --trusted-host pypi.python.org -r requirements.txt
RUN apt-get update && apt-get install -y python3-minimal python3-pip openssh-client
RUN pip3 install pyotp python-pam pypng pyqrcode

# Make port 80 available to the world outside this container
EXPOSE 8080

# Define environment variable
#ENV MAXMSGLEN 2048
ENV CERTNAME demosshuserca 
#ENV DEMOMODE True

# Run main.py when the container launches
CMD ["python3", "main.py"] 
