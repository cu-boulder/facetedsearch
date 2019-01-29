import json
import requests
import os
import argparse

from datetime import datetime

parser = argparse.ArgumentParser()
parser.add_argument('--index', default='webex-v2', help='name of the index. Default=webex-v2')
args = parser.parse_args()
index=args.index


updatedate=datetime.now()
statusfile='/data/web/htdocs/experts/status/' + index + '.html'
esurl='http://localhost:9200/'+ index + '/_search?search_type=count'

if os.path.isfile(statusfile):
  os.remove(statusfile)

counts = json.dumps({"aggs": {"count_by_type": {"terms": {"field": "_type"}}}})
response=requests.get(esurl, data=counts)
results=json.loads(response.text)
indexcount=results['hits']['total']
if ( indexcount < 1 ):
  exit()

f = open(statusfile,'w')

message = """<html>
<head></head>
<body><p>index count=""" + str(indexcount) + """<BR>Update Time: """ + str(updatedate) + """</p></body>
</html>"""

f.write(message)
f.close()
