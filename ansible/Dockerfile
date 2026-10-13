# "ansible-docker-lab" control container: Ansible 2.10.x + Docker SDK + docker CLI
FROM ubuntu:22.04
ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update && apt-get install -y --no-install-recommends \
        ansible python3 python3-docker docker.io ca-certificates \
    && rm -rf /var/lib/apt/lists/*
# collection that provides docker_container / docker_volume modules
RUN ansible-galaxy collection install community.docker || true
CMD ["sleep", "infinity"]
