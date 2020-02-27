import json
import boto3
import search_edgar as se
import extract
from datetime import datetime


def batch(event, content):
    try:
        payload = event['Records'][0]['Sns']['Message']
        print("Message from batch: {}".format(payload))
        count = int(payload)
        assert(count >= 1)
    except Exception as e:
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
    print("{}: {}".format(name, dur))
    return None


def process_ten_k(event, context):
    payload = event['Records'][0]['Sns']['Message']
    req = json.loads(payload)
    tenK = req.get('TenK')
    extract.process_10K(tenK)

