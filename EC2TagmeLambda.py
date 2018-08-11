import boto3
import json

def Tagme(event, context):
    # TODO implement
    client = boto3.client('ec2', region_name='us-east-1')
    msg = json.loads(event['Records'][0]['Sns']['Message'])
    instance_id = msg['EC2InstanceId']
    print (instance_id)
    response = client.create_tags (Resources=[instance_id], Tags=[{'Key': 'Name', 'Value': 'my instance'}])
    return "The return response:", response