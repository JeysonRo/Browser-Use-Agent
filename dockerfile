FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive
ENV DISPLAY=:1

# Install system dependencies and Chromium
RUN apt-get update && apt-get install -y \
    software-properties-common \
    curl \
    wget \
    git \
    x11vnc \
    xvfb \
    xfce4 \
    chromium-browser \
    novnc \
    build-essential \
    libssl-dev \
    zlib1g-dev \
    libbz2-dev \
    libreadline-dev \
    libsqlite3-dev \
    libncurses5-dev \
    libncursesw5-dev \
    libffi-dev \
    liblzma-dev \
    tk-dev \
    xz-utils \
    lsb-release \
    ca-certificates \
    make \
    gcc \
    nano \
    net-tools

# Build Python 3.12.3 from source
WORKDIR /opt
RUN curl -O https://www.python.org/ftp/python/3.12.3/Python-3.12.3.tgz && \
    tar -xzf Python-3.12.3.tgz && \
    cd Python-3.12.3 && \
    ./configure --enable-optimizations && \
    make -j$(nproc) && \
    make altinstall

RUN ln -sf /usr/local/bin/python3.12 /usr/bin/python

# Install pip for Python 3.12
RUN curl -sS https://bootstrap.pypa.io/get-pip.py | python

# Install supervisor using pip to make sure it's Python 3.12-compatible
RUN pip install supervisor websockify


# Setup VNC password
RUN mkdir -p ~/.vnc && \
    x11vnc -storepasswd 1234 ~/.vnc/passwd


# Supervisor configuration for GUI + VNC + noVNC
# Replace launch.sh with direct websockify command
RUN echo "[supervisord]\nnodaemon=true\n" > /etc/supervisord.conf && \
    echo "[program:Xvfb]\ncommand=/usr/bin/Xvfb :1 -screen 0 1024x576x16" >> /etc/supervisord.conf && \
    # echo "[program:Xvfb]\ncommand=/usr/bin/Xvfb :1 -screen 0 1920x1080x24" >> /etc/supervisord.conf && \
    echo "\n[program:x11vnc]\ncommand=/usr/bin/x11vnc -forever -usepw -display :1 -passwd 1234" >> /etc/supervisord.conf && \
    echo "\n[program:xfce4]\ncommand=startxfce4" >> /etc/supervisord.conf && \
    echo "\n[program:novnc]" >> /etc/supervisord.conf && \
    echo "command=/usr/local/bin/websockify 6080 localhost:5900 --web=/usr/share/novnc" >> /etc/supervisord.conf && \
    echo "\n[program:chromium]" >> /etc/supervisord.conf && \
    echo "command=chromium-browser --no-sandbox --remote-debugging-address=0.0.0.0 --remote-debugging-port=9222" >> /etc/supervisord.conf



# Make python3.12 the default
RUN ln -sf /usr/local/bin/python3.12 /usr/bin/python && \
ln -sf /usr/local/bin/python3.12 /usr/bin/python3

# Create working directory
WORKDIR /root

# Copy necessary files and  install dependencies
COPY test.py /root/
COPY .env /root/
COPY requirements.txt /root/
RUN pip install -r requirements.txt
RUN python -m playwright install chromium

# Create default files


# Note: Since we're using default files, the user can still mount their own files
# when needed using docker run -v command, but they're not required anymore

EXPOSE 6080 9222

CMD ["/usr/local/bin/supervisord", "-c", "/etc/supervisord.conf"]


# run this
# docker build -t browser .
# docker build --platform=linux/amd64 -t browser-vnc .
# docker run -d -p 6080:6080 -p 9222:9222 --name browser-container browser

# docker rm browser-container
# docker run -d -p 6080:6080 -p 9222:9222 --name browser-container browser   

# go into docker container using [docker exec -it browser-container bash]
# apt update and ensure python3 and python3-pip are installed
# pip install playwright browser-use

# Simple run command (no volume mounts needed anymore):
# docker run -d -p 6080:6080 -p 9222:9222 --name browser-container browser
#
# Optional: still mount custom files if needed:
# docker run -d -p 6080:6080 -p 9222:9222 --name browser-container -v "$(pwd)/test.py:/root/test.py" -v "$(pwd)/.env:/root/.env" browser