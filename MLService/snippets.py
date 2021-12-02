from google.cloud import storage
client = storage.Client()
bucket = client.get_bucket('bts-data-atss')
blob = bucket.blob('Result/11_21_21.csv')
blob.upload_from_filename('Result/11_21_21.csv')