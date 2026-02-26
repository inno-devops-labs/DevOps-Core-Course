FROM python:3.11-slim

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        openssh-client \
        sshpass \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir \
    ansible \
    docker

RUN mkdir -p /root/.ssh

WORKDIR /ansible

# Copy ansible.cfg to a safe (non-world-writable) location
COPY ansible.cfg /etc/ansible/ansible.cfg
ENV ANSIBLE_CONFIG=/etc/ansible/ansible.cfg

# Entrypoint fixes SSH key permissions (Windows → Linux)
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh
ENTRYPOINT ["/entrypoint.sh"]
