
import requests
import json
import random

API_ENDPOINT = "http://192.168.1.117:8080/retrain"


if __name__ == '__main__':
    # Start up the server to expose the metrics.

    # Generate some requests.
    # while True:
        # data to be sent to api
    param = {
    "file_name": json.dumps("Result/12_06_21.csv")
    }
    # sending post request and saving response as response object
    response = requests.post(url = API_ENDPOINT, data = param)

    # result = response.json()
    # extracting response text 
    print(response)

