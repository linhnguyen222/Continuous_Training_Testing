# start rabbitmq
cd /home/linh/Advanced_SS_project/MLService/rmq_docker
docker build -t rabbitmq:3.9-consistent_hash_x_enabled .

docker run -d --rm --name rabbitmq -p 5672:5672 -p 15672:15672 rabbitmq:3.9-consistent_hash_x_enabled

gcloud container clusters create bts-cluster --zone europe-north1-a --num-nodes 2 --machine-type=e2-micro
# https://cloud.google.com/artifact-registry/docs/docker/pushing-and-pulling#linux
gcloud auth configure-docker europe-north1-docker.pkg.dev
docker-credential-gcr configure-docker europe-north1-docker.pkg.dev

europe-north1-docker.pkg.dev/steel-climber-303808/btscontainer/bts_server:latest

docker tag bts_server europe-north1-docker.pkg.dev/steel-climber-303808/btscontainer/bts_server:latest
docker push europe-north1-docker.pkg.dev/steel-climber-303808/btscontainer/bts_server:latest

# 
export GOOGLE_APPLICATION_CREDENTIALS="/Users/nguyenlinh/Macadamia/Advanced_SS_project/MLService/steel-climber-303808-7df11bf1a845.json"