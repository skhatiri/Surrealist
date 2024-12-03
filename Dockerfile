FROM skhatiri/aerialist:k8s
RUN pip3 install -e /src/aerialist/

#install Surrealist
COPY ./requirements.txt /src/surrealist/requirements.txt
WORKDIR /src/surrealist/
RUN pip3 install -r /src/surrealist/requirements.txt

COPY ./ /src/surrealist/
COPY ./template.env /src/surrealist/.env

ENV ROS_KUBE_TEMPLATE /src/aerialist/aerialist/resources/k8s/k8s-job-avoidance.yaml
ENV KUBE_TEMPLATE /src/aerialist/aerialist/resources/k8s/k8s-job.yaml
