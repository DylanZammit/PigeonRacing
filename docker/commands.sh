# start afresh or delete minikube cluster for the following line to take affect
minikube delete --all
minikube start --insecure-registry=<HOST_IP>:5000

# create local docker registry
docker run -d -p 5000:5000 --restart=always --name registry registry:2

# build and push data-load image to local registry
docker build -t localhost:5000/pigeon-data-load:latest -f docker/data_load/Dockerfile .
docker push localhost:5000/pigeon-data-load:latest

# build and push model image to docker hub
docker build -t localhost:5000/pigeon-data-model:latest -f docker/data_model/Dockerfile .
docker push localhost:5000/pigeon-data-model:latest

# create kubernetes pods + services + namespaces
kubectl create -f namespaces/pigeon-racing-prd.yaml
kubectl create -f services/clickhouse.yaml
kubectl create -f pods/clickhouse.yaml
kubectl create -f pods/data-load.yaml
kubectl create -f pods/data-model-velocity.yaml
