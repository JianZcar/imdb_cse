# Use an Ubuntu base image
FROM ubuntu:latest

# Set the maintainer label
LABEL maintainer="esteban.jianzcar@outlook.com"

# Install dependencies, add deadsnakes PPA, and install multiple Python versions
RUN apt-get update && apt-get install -y \
    software-properties-common \
    && add-apt-repository ppa:deadsnakes/ppa \
    && apt-get update && apt-get install -y \
    python3.8 \
    python3.9 \
    python3.10 \
    python3.11 \
    python3.12 \
    python3-pip \
    && rm -rf /var/lib/apt/lists/*

# Set the working directory
WORKDIR /workspace

# Configure alternatives to select Python version
RUN update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.8 5 \
    && update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.9 4 \
    && update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.10 3 \
    && update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.11 2 \
    && update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.12 1

# Set the default Python version (optional)
RUN update-alternatives --config python3

# Set default command to run Python
CMD ["python3"]

