FROM debian:bookworm-slim

RUN apt update && apt install -y \
    openssh-server \
    binutils \
    file \
    bsdmainutils \
    ssdeep \
    python3 \
 && rm -rf /var/lib/apt/lists/*
RUN mkdir -p /run/sshd
RUN echo "PermitRootLogin yes" >> /etc/ssh/sshd_config
RUN echo "PubkeyAuthentication yes" >> /etc/ssh/sshd_config

EXPOSE 22

CMD ["/usr/sbin/sshd", "-D"]