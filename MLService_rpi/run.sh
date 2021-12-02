# start rabbitmq
cd /home/linh/Advanced_SS_project/MLService/rmq_docker
docker build -t rabbitmq:3.9-consistent_hash_x_enabled .

docker run -d --rm --name rabbitmq -p 5672:5672 -p 15672:15672 rabbitmq:3.9-consistent_hash_x_enabled

