# start afresh or delete minikube cluster for the following line to take affect
minikube delete --all
minikube start --insecure-registry=<HOST_IP>:5000

# In separate terminals and must be left open if on windows
minikube tunnel
minikube mount path/to/code/of/PigeonRacing:/PigeonRacing

# create local docker registry
docker run -d -p 5000:5000 --restart=always --name registry registry:2

# build and push data-load image to local registry
docker build -t localhost:5000/pigeon-data-load:latest -f docker/data_load/Dockerfile .
docker push localhost:5000/pigeon-data-load:latest

# build and push model image to docker hub
docker build -t localhost:5000/pigeon-data-model:latest -f docker/data_model/Dockerfile .
docker push localhost:5000/pigeon-data-model:latest

# create kubernetes pods + services + namespaces
kubectl create -f kubernetes/namespaces/pigeon-racing-prd.yaml

kubectl create -f kubernetes/services/clickhouse.yaml
kubectl create -f kubernetes/pods/clickhouse.yaml

kubectl create -f kubernetes/pods/data-load.yaml
kubectl create -f kubernetes/pods/data-model-velocity.yaml

kubectl create -f kubernetes/services/mlflow.yaml
kubectl create -f kubernetes/pods/mlflow.yaml
