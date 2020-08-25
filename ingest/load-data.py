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

parser = argparse.ArgumentParser()
parser.add_argument('--spooldir', default='./spool', help='where to read files from')
parser.add_argument('out', metavar='OUT', help='elasticsearch bulk ingest file format eg allpubs.idx')
args = parser.parse_args()

bulkfiles=args.spooldir + '/' + args.out + '*'
#index="fispubs-setup-news"
index="fispubs"



host = 'search-experts-pubs-unoedenr36fpm7alfpboeihcnq.us-east-2.es.amazonaws.com'
service = 'es'
region = 'us-east-2'

credentials = boto3.Session().get_credentials()
awsauth = AWS4Auth(credentials.access_key, credentials.secret_key, region, service, session_token=credentials.token)

es = Elasticsearch(
    hosts = [{'host': host, 'port': 443}],
    http_auth = awsauth,
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
  print(f)
  with open(f) as json_file:
    json_docs=json_file.read()
    es.bulk(json_docs)
    time.sleep(5)
