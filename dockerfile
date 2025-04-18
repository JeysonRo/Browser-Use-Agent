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
    echo "[program:Xvfb]\ncommand=/usr/bin/Xvfb :1 -screen 0 1280x720x16" >> /etc/supervisord.conf && \
    echo "\n[program:x11vnc]\ncommand=/usr/bin/x11vnc -forever -usepw -display :1 -passwd 1234" >> /etc/supervisord.conf && \
    echo "\n[program:xfce4]\ncommand=startxfce4" >> /etc/supervisord.conf && \
    echo "\n[program:novnc]" >> /etc/supervisord.conf && \
    echo "command=/usr/local/bin/websockify 6080 localhost:5900 --web=/usr/share/novnc" >> /etc/supervisord.conf



# Make python3.12 the default
RUN ln -sf /usr/local/bin/python3.12 /usr/bin/python && \
ln -sf /usr/local/bin/python3.12 /usr/bin/python3

EXPOSE 6080

CMD ["/usr/local/bin/supervisord", "-c", "/etc/supervisord.conf"]


# run this
# docker build -t browser .
# docker build --platform=linux/amd64 -t browser-vnc .
# docker run -d -p 6080:80 -p 5900:5900 --name browser-container browser

# docker rm browser-container
# docker run -d -p 6080:6080 --name browser-container browser   
# password is 1234

# go into docker container using [docker exec -it browser-container bash]
# apt update and ensure python3 and python3-pip are installed
# pip install playwright browser-use