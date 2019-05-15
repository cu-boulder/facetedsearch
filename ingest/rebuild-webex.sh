# Reworked this to copy the publications index instead of rebuilding it from a SPARQL query
. ./vivoapipw.py
sourceindex=$PUBSINDEX
targetindex=$WEBEXINDEX
echo "Copying $sourceindex to $targetindex"
echo "Index counts prior to run" 
#./idx_get_count.sh $targetindex 
curl -XDELETE localhost:9200/${targetindex}
curl -X POST "localhost:9200/_reindex" -H 'Content-Type: application/json' -d'
{
  "source": {
    "index": "'${sourceindex}'"
  },
  "dest": {
    "index": "'${targetindex}'"
  }
}
'
sleep 10
echo "Index counts after run" 
#./idx_get_count.sh $targetindex
