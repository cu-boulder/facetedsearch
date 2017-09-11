# get counts of index prior to deletion
./idx_get_count.sh > idx_counts-prior.out
curl -XDELETE localhost:9200/fis
curl -XPUT localhost:9200/fis
curl -XPUT 'localhost:9200/fis/person/_mapping?pretty' --data-binary @mappings/person.json
curl -XPUT 'localhost:9200/fis/equipment/_mapping?pretty' --data-binary @mappings/equipment.json
curl -XPOST 'localhost:9200/_bulk' --data-binary @people-fix.list
