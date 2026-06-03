FROM debian:bookworm-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    openssh-server \
    binutils \
    file \
    bsdmainutils \
    ssdeep \
    yara \
    python3 \
    procps \
    xxd \
    radare2 \
    libimage-exiftool-perl \
 && rm -rf /var/lib/apt/lists/*

RUN mkdir -p /run/sshd /samples \
 && echo "PermitRootLogin yes"          >> /etc/ssh/sshd_config \
 && echo "PubkeyAuthentication yes"     >> /etc/ssh/sshd_config \
 && echo "PasswordAuthentication no"    >> /etc/ssh/sshd_config

COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

EXPOSE 22

ENTRYPOINT ["/entrypoint.sh"]
CMD ["/usr/sbin/sshd", "-D", "-e"]
