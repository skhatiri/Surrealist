# must run from parent directory, where aerialist is also a subfolder
FROM ubuntu:latest

RUN apt-get update \
    && apt-get install -y wget curl python3-pip python3-dev \
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

# setup source code
COPY ./Aerialist/ /src/aerialist
RUN pip3 install -e /src/aerialist
COPY ./Flight2Sim/requirements.txt /src/flight2sim/requirements.txt
WORKDIR /src/flight2sim/
RUN pip3 install -r requirements.txt
COPY ./Flight2Sim .
# RUN chmod +x ./Flight2Sim/__main__.py
COPY ./Flight2Sim/k8s-config.yaml /root/.kube/config
COPY ./Flight2Sim/template.env ./.env
RUN mkdir -p /io/ ./results/logs/

