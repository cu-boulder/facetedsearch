# get counts of index prior to deletion
dstamp=`date +%Y%m%e-%H%M%S`
mkdir spool/$dstamp
outfile="spool/${dstamp}/rebuild-index.out"
echo "CREATING ES DOCUMENTS" > $outfile
python ./ingest-people.py spool/$dstamp/people.list  >> $outfile 2>&1
python ./ingest-equipment.py spool/$dstamp/equipment.list >> $outfile 2>&1
echo "Index counts prior to run" >> $outfile
./idx_get_count.sh >> $outfile
curl -XDELETE localhost:9200/fis >> $outfile
curl -XPUT localhost:9200/fis >> $outfile
curl -XPUT 'localhost:9200/fis/person/_mapping?pretty' --data-binary @mappings/person.json >> $outfile
curl -XPUT 'localhost:9200/fis/equipment/_mapping?pretty' --data-binary @mappings/equipment.json >> $outfile
curl -XPOST 'localhost:9200/_bulk' --data-binary @spool/$dstamp/people.list >> $outfile 2>&1
curl -XPOST 'localhost:9200/_bulk' --data-binary @spool/$dstamp/equipment.list >> $outfile 2>&1
sleep 10
echo "Index counts after run" >> $outfile
./idx_get_count.sh >> $outfile 2>&1
