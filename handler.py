import json
import boto3
import search_edgar as se
import extract
from datetime import datetime

def hello(event, context):
    client = boto3.client('s3')
    client.list_objects(Bucket='fylterus-tweets')

    body = {
        "message": "Go Serverless v1.0! Your function executed successfully!",
        "input": event
    }

    response = {
        "statusCode": 200,
        "body": json.dumps(body)
    }

    return response

def batch(event, content):
    try:
        payload = event['Records'][0]['Sns']['Message']
        print(payload)
        count = int(payload)
        assert(count >= 1)
    except:
        count = 5 

    se.marshal(count) 


def sec_fetch(event, context):
    now = datetime.now()
    payload = event['Records'][0]['Sns']['Message']
    req = json.loads(payload)
    name = req.get('Company')
    docs = req.get('Documents')
    dest = req.get('Destination')

    se.process(name, docs, dest) 

    fin = datetime.now()
    dur = fin - now
    print(name, dur)
    return None

def process_ten_k(event, context):
    payload = event['Records'][0]['Sns']['Message']
    req = json.loads(payload)
    tenK = req.get('TenK')
    extract.process_10K(tenK)

