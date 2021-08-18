from elasticsearch import Elasticsearch, RequestsHttpConnection
from elasticsearch.helpers import parallel_bulk
from collections import deque
from requests_aws4auth import AWS4Auth
from datetime import datetime
import boto3
import glob
import json
import os, time
import argparse

## Parse and set parameter values

parser = argparse.ArgumentParser()
parser.add_argument('--spooldir', default='./spool', help='where to read files from')
parser.add_argument('--esendpoint', default='search-experts-direct-cz3fpq4rlxcbn5z27vzq4mpzaa.us-east-2.es.amazonaws.com', help='AWS Elasticsearch enddpoint')
parser.add_argument('--esservice', default='es', help='AWS Elastic enddpoint service')
parser.add_argument('--esuser', default='', help='AWS Elastic master user')
parser.add_argument('--espass', default='', help='AWS Elastic master password')
parser.add_argument('--esregion', default='us-east-2', help='AWS Elasticsearch enddpoint region')
parser.add_argument('--index', default='fispubs', help='Elasticsearch index name')
parser.add_argument('--out', default='allpubs.idx', metavar='OUT', help='elasticsearch bulk ingest file format eg allpubs.idx')
args = parser.parse_args()

bulkfiles=args.spooldir + '/' + args.out + '*'
index=args.index
host = args.esendpoint
service = args.esservice
region = args.esregion
user = args.esuser
password = args.espass

#Setup AWS Elastic Authentication. 
# The credential needs to be placed in the .aws directory under the home directory of the user running this. Similar to .ssh

credentials = boto3.Session().get_credentials()
awsauth = AWS4Auth(credentials.access_key, credentials.secret_key, region, service, session_token=credentials.token)

es = Elasticsearch(
    hosts = [{'host': host, 'port': 443}],
    http_auth = (user,password),
    use_ssl = True,
    verify_certs = True,
    connection_class = RequestsHttpConnection
)

# Example of a single document upload, for future
#doc = {
#    'author': 'kimchy2',
#    'text': 'Elasticsearch: cool. bonsai cool.',
#    'timestamp': datetime.now(), 
#         }
#res = es.index(index="test-index", id=2, body=doc)
#print(res['result'])


es.indices.delete(index=index, ignore=[400, 404])

for f in glob.iglob(bulkfiles):
  print("File: ",f)
  with open(f) as json_file:
    json_docs=json_file.read()
    print("About to load: ", f)
    es.bulk(json_docs, request_timeout=30)
    print("finished loading: ", f)
    time.sleep(5)
    print("finished sleeping")
