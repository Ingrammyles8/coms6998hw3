import json
import boto3
import datetime 
from elasticsearch import Elasticsearch, RequestsHttpConnection
from aws_requests_auth.aws_auth import AWSRequestsAuth
from aws_requests_auth.boto_utils import BotoAWSRequestsAuth

print("Admin access is king")

PHOTOS_BUCKET = "coms6998hw3b2"

def detect_labels(fileName):

	client = boto3.client('rekognition')
	response = client.detect_labels(Image={'S3Object':{'Bucket':PHOTOS_BUCKET,'Name':fileName}},
		MaxLabels=10)

	labels = response['Labels']
	returnLabels = [label['Name'] for label in labels]
	return returnLabels
	
def uploadLabelsIntoES(labels, fileName):

	item = {"objectKey": fileName,
	"bucket": PHOTOS_BUCKET,
	"createdTimestamp": datetime.datetime.now().strftime("%Y-%m-%d:%H-%M-%S"),
	"labels": labels
	}
	
	host = 'search-public-photos-o6fphjtmcgy3eqsb2nriuqefsq.us-east-1.es.amazonaws.com'
	auth = BotoAWSRequestsAuth(aws_host=host,
                           aws_region='us-east-1',
                           aws_service='es')

	# use the requests connection_class and pass in our custom auth class
	es_client = Elasticsearch(hosts = [{'host': host, 'port': 443}],
						  connection_class=RequestsHttpConnection,
						  http_auth=auth,
						  use_ssl=True,
						  verify_certs=True)
	
	response = es_client.index(index = "public-photos", body = item)
	print(response)

	
def lambda_handler(event, context):

	fileName = event["Records"][0]["s3"]["object"]["key"]
	labels = detect_labels(fileName)
	uploadLabelsIntoES(labels, fileName)
	
	return {
		'statusCode': 200,
		'body': json.dumps('Hello from Lambda!')
	}


