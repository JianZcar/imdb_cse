FROM ubuntu:latest

LABEL maintainer="esteban.jianzcar@outlook.com"

WORKDIR /workspace

RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    libssl-dev \
    zlib1g-dev \
    libbz2-dev \
    libreadline-dev \
    libsqlite3-dev \
    wget \
    llvm \
    libncurses5-dev \
    libncursesw5-dev \
    xz-utils \
    tk-dev \
    libffi-dev \
    liblzma-dev \
    git \
    && rm -rf /var/lib/apt/lists/*

# Install pyenv
ENV PYENV_ROOT="/root/.pyenv" \
    PATH="/root/.pyenv/bin:/root/.pyenv/shims:/root/.pyenv/versions:$PATH"
RUN git clone https://github.com/pyenv/pyenv.git $PYENV_ROOT \
    && $PYENV_ROOT/plugins/python-build/install.sh \
    && echo 'eval "$(pyenv init --path)"' >> ~/.bashrc \
    && echo 'eval "$(pyenv init -)"' >> ~/.bashrc

# Install multiple Python versions
RUN pyenv install 3.9 \
    && pyenv install 3.10 \
    && pyenv install 3.11 \
    && pyenv global 3.9 3.10 3.11

# Verify installation
RUN pyenv versions

# Set the default command
CMD ["bash"]
