# Jenkins with the Docker CLI so pipeline stages can run `docker build/run/exec`
FROM jenkins/jenkins:lts-jdk17
USER root
RUN apt-get update && apt-get install -y --no-install-recommends docker.io \
    && rm -rf /var/lib/apt/lists/*
USER root
