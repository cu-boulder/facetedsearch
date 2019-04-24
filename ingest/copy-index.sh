
curl -X POST "localhost:9200/_reindex" -H 'Content-Type: application/json' -d'
{
  "source": {
    "index": "fispubs-v1"
  },
  "dest": {
    "index": "fispubsnews-v1"
  }
}
'


