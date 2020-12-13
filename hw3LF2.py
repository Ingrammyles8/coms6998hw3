import json
import boto3
import re
from elasticsearch import Elasticsearch, RequestsHttpConnection
from aws_requests_auth.boto_utils import BotoAWSRequestsAuth


ELASTICSEARCH_INDEX = "public-photos"
def queryLex(query):
	'''
	Parse out the user's query into separate terms.
	
	Args:
		query (str): The user input, sent by the API.
	Returns:
		terms (array): The parsed terms. Can be of length 0 to 3.
	'''

	print("querying lex for {}".format(query))
	client = boto3.client('lex-runtime')#, region_name = "us-east-1")
	print("accessed client")
	print(client)

	### Commented out for testing. This is timing out for some reason.
	response = client.post_text(
		botName='PictureSearch',
		botAlias='Beta',
		userId='userId',
		inputText = query
		)
	print(response)
	### Testing:
	#response = {"slots": {"slotOne": "Human", "slotTwo": "Dog", "slotThree": None} }
	
	# Some of these may be None
	term1 = response["slots"]["slotOne"]
	term2 = response["slots"]["slotTwo"]
	term3 = response["slots"]["slotThree"]
	
	terms = [term1, term2, term3]
	terms = [term for term in terms if term] # Get rid of the None ones
	print(terms)
	return terms

def getPhotosFromESforOneTerm(es_client, term):
	'''
	Query ES for terms.
	Args:
		es_client (LexRuntimeService object): An initialized object.
		term (str): Individual term to query ES with.
	Returns:
		fileNames (set of strings): The filenames listed in ES whose photos
			have the input term in their Rekognition labels.
	'''
	response = es_client.search(index=ELASTICSEARCH_INDEX, body={
										  "query": {
										    "match": {
										      "labels": term
										      }
										    }
										  }
								)
	items = response["hits"]["hits"]
	fileNames = set([item["_source"]["objectKey"] for item in items])
	return fileNames
	
  
def getPhotosFromES(terms):
	'''
	Search Elasticsearch using the input terms.
	Return the filenames of photos that match the search.
	Args:
		terms (array of strings): Can be strings or None.
	Returns:
		photos (json object): Json list of photo file names.
	'''
	
	print ("Querying Elasticsearch")
	host = "search-public-photos-o6fphjtmcgy3eqsb2nriuqefsq.us-east-1.es.amazonaws.com"
	credentials = boto3.Session().get_credentials()
	auth = BotoAWSRequestsAuth(aws_host=host,
                           aws_region='us-east-1',
                           aws_service='es')
	# use the requests connection_class and pass in our custom auth class
	es_client = Elasticsearch(hosts = [{'host': host, 'port': 443}],
						  connection_class=RequestsHttpConnection,
						  http_auth=auth,
						  use_ssl=True,
						  verify_certs=True)

	fileNames = set()
	for term in terms:
		fileNames |= getPhotosFromESforOneTerm(es_client, term)
	print ("fileNames:")
	print (fileNames)
	return fileNames


def lambda_handler(event, context):
	
	print("starting")
	print(event)
	query = event["body"]
	match = re.search("(?:search=)(.+)",query)
	query_string = match.group(1)
	print(query_string)
	query_string = query_string.replace("+"," ")
	print(query_string)
	terms = queryLex(query_string)
	if len(terms) == 0:
		print ("Lex did not find any search terms.")
		# todo
		return 404
	fileNames = getPhotosFromES(terms)
	if len(fileNames) == 0:
		print ("ES did not find any matching photos.")
		# todo
		return 404		
	
	
	return {
		'statusCode': 200,
		'body': json.dumps(['https://coms6998hw3b2.s3.amazonaws.com/{}'.format(f) for f in fileNames]) # todo return photos
	}
