curl "localhost:9200/fis/_search?search_type=count" -d '{
    "aggs": {
        "count_by_type": {
            "terms": {
                "field": "_type"
            }
        }
    }
}'
