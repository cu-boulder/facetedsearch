# get counts of index prior to deletion
. ./vivoapipw.py
dstamp=`date +%Y%m%d-%H%M%S`
#dstamp="20190111-152317"
#dstamp="20190117-171900"
indexname=$PEOPLEINDEX
mkdir spool/$dstamp
outfile="spool/${dstamp}/rebuild-index.out"
echo "CREATING ES DOCUMENTS" # > $outfile
python ./ingest-people.py --index ${indexname} --sparql ${ENDPOINT} spool/$dstamp/people.list   #>> $outfile 2>&1
./idx_get_count.sh ${indexname} #>> $outfile
curl -XDELETE localhost:9200/${indexname} #>> $outfile
curl -XPUT localhost:9200/${indexname} #>> $outfile
curl -XPUT localhost:9200/${indexname}/person/_mapping?pretty --data-binary @mappings/person.json #>> $outfile
curl -XPOST localhost:9200/_bulk --data-binary @spool/$dstamp/people.list #>> $outfile 2>&1
sleep 10
echo "Index counts after run" #>> $outfile
./idx_get_count.sh #>> $outfile 2>&1
