indexname=$1
curl -H 'Content-Type: application/json' "localhost:9200/${indexname}/_search" -d '{
    "size": 0,
    "aggs": {
        "count_by_type": {
            "terms": {
                "field": "_type"
            }
        }
    }
}'
