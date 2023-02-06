FROM ubuntu:latest

RUN apt-get update \
    && apt-get install -y git wget curl python3-pip python3-dev \
    && cd /usr/local/bin \
    && ln -s /usr/bin/python3 python \
    && pip3 install --upgrade pip

# install kubectl
RUN curl -sLS https://get.arkade.dev | sh \
    && arkade get kubectl \
    && mv -v /root/.arkade/bin/kubectl /usr/bin/

# install yq
RUN wget https://github.com/mikefarah/yq/releases/download/v4.22.1/yq_linux_amd64 -O /usr/bin/yq &&\
    chmod +x /usr/bin/yq

#install Surrealist
COPY ./requirements.txt /src/surrealist/requirements.txt
WORKDIR /src/surrealist/
RUN pip3 install -r /src/surrealist/requirements.txt
COPY ./k8s-config.yaml /root/.kube/config

COPY ./ /src/surrealist/
COPY ./template.env /src/surrealist/.env

RUN mkdir -p /io/ ./results/logs/

