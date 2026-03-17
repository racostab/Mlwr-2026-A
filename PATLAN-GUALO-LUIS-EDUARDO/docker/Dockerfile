FROM kalilinux/kali-rolling:latest

RUN apt-get update && apt-get upgrade -y && \
    apt-get install -y \
    kali-linux-headless \
    && rm -rf /var/lib/apt/lists/*

CMD ["/bin/bash"]
