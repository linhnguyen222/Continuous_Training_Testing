# Continuous Training and continuous testing
## Overview
The project illustrates the continuous training approach for an end-to-end ML system for predictive maintenance. 



## Architecture
### Design

![The original design](./figures/Original_design.drawio.png)
In the design, the system contain 3 core components: data streaming, ML inference, and retraining of the ML model. The dataset used in this project is from the BTS dataset, divided by into small time windows, each consists of one day of power grid data, from a single station. The model is developed using LSTM, and is retrained with the new data that were collected and sent to the server for inference on the previous day, everyday. The in-use model will be replaced by the new model if the new model outperform the old model on the test dataset.

The data streaming is running either locally or on a rapsberry pi, the prediction server is deployed as a container on GCP Kubernetes Engine, the retraining is running locally and scheduled to run everyday using Airflow, the data streaming and the server are communicating through a Rabbitmq exchange host on [CloudAMQP](https://www.cloudamqp.com/). The inference result is saved on GCP cloud storage, and downloaded for retraining.

Currently, I am trying to de-couple the retraining and the prediction server.
<!-- ### Current version
[The current design](./figures/Current_version.drawio.png)

In the current version, the retrain is done within the kubernetes node.

The container works fine locally, however, the fit function crash on gcp KE, and it's not obvious to me how to debug this. -->
![Fit function crash](./figures/crash-fit-function.png)
## Demo
Since the server is deployed on GCP, we can try streaming the data by cloning the repository, installing pika, then running:
```
    python3 data_streaming/run_streaming.py
```
## How to scale with multiple model:
There are 2 ways of scaling the current architecture. Depending on the characteristic, and requirements of the service, we can scale the service either vertically or horizontally.

If the service only consists of a few of models, given that the training time of our model is not very significant, e.g: only a couple of minutes, we can scale the system vertically, and retrain all the model in the same node. Thus, once a new file is uploaded with an identification tag for a specific model, we look up the configuration for the given model which might contain the deployment information, and retrain, and deploy the model accordingly. With this vertical training approach, since the training time and deployment for each of our model is quite short, only a couple of minutes, eg 3 minutes (2 minutes to retrain, and 1 minutes to be pushed to the Artifact Registry), if we have 5 models, in the worst case scenario, they all require to be retrained at the same time, then it takes only 15 minutes for the last model in the queue to be retrained, and deployed, which is still an exceptable amount of time.

However, in case we have a very large amount of models, or/and each of them takes a significant amount of time to be retrained, the vertical training approach is not applicable anymore, because it would take too much time for some models in the queue to be retrained. Possibly, the models are already due for another retrain before they get retrained for the first time. Thus, in this case, we would adopt a horizontal scaling approach. That means we would add additional nodes or machine to handle the traffic, and ensure reasonable model retraining time. This can be done through having a several node on a cluster, and have a load balancer to distribute retrain request, or having a designate node for a single or a few models.

## Reflection
### The most challenging aspect

The most challenging aspect in this project for me was debugging container running on Kubernetes Engine. Because unlike local machine or a standard local machine where you can log in and debug your code directly, most of the debugging is done though the Kubernetes log on GCP, and I have to containerize and deploy the new container everytime a change or a new log is added for the debugging purpose, which is very time consuming. On top of that, in my experience, the logging system on Kubernetes Engine on GCP does not work correctly, and sometimes terminate the process before all the logs were printed out, therefore, can be very misleading on whether the code is ran correctly. This issue is currently dealt with using `sys.stdout.flush()`.

### The most interesting aspect

The most interesting challenge in the project is that the input need to be normalised according to the mean and max values of the data used to current serving LSTM model. Thus, doing data preprocessing from the client front can cause misleading result, because the model can be replaced quite often. To overcome this, the data normalization is currently handled in the server, where mean and max is always updated.