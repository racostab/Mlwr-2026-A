FROM debian:bookworm-slim
ARG R2_VERSION=6.1.6

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
    libimage-exiftool-perl \
    ca-certificates \
    curl \
 && ARCH="$(dpkg --print-architecture)" \
 && curl -fsSL -o /tmp/radare2.deb \
      "https://github.com/radareorg/radare2/releases/download/${R2_VERSION}/radare2_${R2_VERSION}_${ARCH}.deb" \
 && apt-get install -y --no-install-recommends /tmp/radare2.deb \
 && rm -f /tmp/radare2.deb \
 && apt-get purge -y --auto-remove curl \
 && rm -rf /var/lib/apt/lists/*

# /samples es scratch efímero: el engine envía cada muestra por SFTP (ya no hay
# volumen compartido). /rules lleva las reglas YARA que usa el analizador `yara`.
RUN mkdir -p /run/sshd /samples \
 && echo "PermitRootLogin yes"          >> /etc/ssh/sshd_config \
 && echo "PubkeyAuthentication yes"     >> /etc/ssh/sshd_config \
 && echo "PasswordAuthentication no"    >> /etc/ssh/sshd_config

COPY sandbox/reglas_yara/ /rules/

COPY user_data/sandbox/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

EXPOSE 22

ENTRYPOINT ["/entrypoint.sh"]
CMD ["/usr/sbin/sshd", "-D", "-e"]
