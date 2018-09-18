import json
import requests
import os

from datetime import datetime

statusfile='/data/web/htdocs/fis-status/webex.html'
os.remove(statusfile)
updatedate=datetime.now()

counts = json.dumps({"aggs": {"count_by_type": {"terms": {"field": "_type"}}}})
response=requests.get('http://localhost:9200/webex-v2/_search?search_type=count', data=counts)
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
