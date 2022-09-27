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
COPY ./requirements.txt /src/drone-experiments/requirements.txt
WORKDIR /src/drone-experiments/
RUN pip3 install -r requirements.txt
COPY . /src/drone-experiments/
RUN chmod +x /src/drone-experiments/run.py
COPY ./k8s-config.yaml /root/.kube/config
COPY ./template.env /src/drone-experiments/.env
RUN mkdir -p /io/ /src/drone-experiments/results/logs/

