export GOOGLE_APPLICATION_CREDENTIALS="/Users/nguyenlinh/Macadamia/Advanced_SS_project/MLService/steel-climber-303808-7df11bf1a845.json"
# containerize server 
docker build -f Dockerfile.server -t bts-server:latest .
# tag and push
docker tag bts-server europe-north1-docker.pkg.dev/steel-climber-303808/btscontainer/bts-server:latest
docker push europe-north1-docker.pkg.dev/steel-climber-303808/btscontainer/bts-server:latest
