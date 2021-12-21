# start rabbitmq
cd /home/linh/Advanced_SS_project/MLService/rmq_docker
docker build -t rabbitmq:3.9-consistent_hash_x_enabled .

docker run -d --rm --name rabbitmq -p 5672:5672 -p 15672:15672 rabbitmq:3.9-consistent_hash_x_enabled
# create kubernete cluster
gcloud container clusters create bts-cluster3 --zone europe-north1-a --num-nodes 2 --machine-type=e2-small

# containerize server 
docker build -f Dockerfile.server -t bts-server:latest .
# https://cloud.google.com/artifact-registry/docs/docker/pushing-and-pulling#linux
# Configurate docker for gcloud
gcloud auth configure-docker europe-north1-docker.pkg.dev
gcloud components install docker-credential-gcr
docker-credential-gcr configure-docker europe-north1-docker.pkg.dev
# name of the container: europe-north1-docker.pkg.dev/steel-climber-303808/btscontainer/bts-server:latest

# tag and push
docker tag bts-server europe-north1-docker.pkg.dev/steel-climber-303808/btscontainer/bts-server:latest
docker push europe-north1-docker.pkg.dev/steel-climber-303808/btscontainer/bts-server:latest
# gg credential
export GOOGLE_APPLICATION_CREDENTIALS="/Users/nguyenlinh/Macadamia/Advanced_SS_project/MLService/steel-climber-303808-7df11bf1a845.json"
# deployment
kubectl apply -f /Users/nguyenlinh/Macadamia/Advanced_SS_project/MLService/deployment/server_deployment.yml