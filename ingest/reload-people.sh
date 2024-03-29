# get counts of index prior to deletion
. ./vivoapipw.py
dstamp=20220817-020001
indexname=$PEOPLEINDEX
#mkdir spool/$dstamp
outfile="spool/${dstamp}/rebuild-index.out"
echo "CREATING ES DOCUMENTS" # > $outfile
#python ./ingest-people.py --index ${indexname} --sparql ${ENDPOINT} spool/$dstamp/people.list   #>> $outfile 2>&1
./idx_get_count.sh ${indexname} #>> $outfile
echo "Deleting index: ${indexname}"
curl -XDELETE localhost:9200/${indexname} #>> $outfile
echo "Creating index: ${indexname}"
curl -XPUT localhost:9200/${indexname} #>> $outfile
#echo "Mapping index: ${indexname}"
#curl -XPUT -H 'Content-Type: application/json' localhost:9200/${indexname}/person/_mapping?pretty --data-binary @mappings/person.json #>> $outfile
echo "Uploading index: ${indexname}"
curl -XPOST -H 'Content-Type: application/json' localhost:9200/_bulk --data-binary @spool/$dstamp/people.list #>> $outfile 2>&1
sleep 10
echo "Index counts after run" #>> $outfile
./idx_get_count.sh #>> $outfile 2>&1
