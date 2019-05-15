. ./vivoapipw.py
indexname=$PUBSINDEX
dstamp=`date +%Y%m%d-%H%M%S`
outdir="spool/${dstamp}"
mkdir $outdir
outfile="${outdir}/rebuild-pubs.out"
echo "CREATING ES DOCUMENTS" > $outfile
python ./ingest-publications.py --index ${indexname} --sparql ${ENDPOINT} --spooldir ${outdir} ${outdir}/allpubs.idx  >> $outfile 2>&1
echo "Index counts prior to run" >> $outfile
./idx_get_count.sh $indexname >> $outfile
curl -XDELETE localhost:9200/${indexname} >> $outfile
curl -XPUT localhost:9200/${indexname} >> $outfile
curl -XPUT -H 'Content-Type: application/json' localhost:9200/${indexname}/publication/_mapping?pretty --data-binary @mappings/publication.json >> $outfile
for f in $outdir/idx-*
do 
   echo $f 
   curl -XPUT -H 'Content-Type: application/json' 'localhost:9200/_bulk' --data-binary @$f >> $outfile 2>&1
done

sleep 10
echo "Index counts after run" >> $outfile
./idx_get_count.sh $indexname >> $outfile 2>&1
