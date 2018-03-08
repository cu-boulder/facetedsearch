indexname=$1
curl "localhost:9200/${indexname}/_search?search_type=count" -d '{
    "aggs": {
        "count_by_type": {
            "terms": {
                "field": "_type"
            }
        }
    }
}'
