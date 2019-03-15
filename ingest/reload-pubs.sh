# get counts of index prior to deletion
# Use this to reload documents that have already been created
# Need to hardcode the dstamp variable of the directory that has the documents
indexname=fispubs-v1
dstamp="20190313-141501"
outdir="spool/${dstamp}"
#mkdir $outdir
outfile="${outdir}/reload-pubs.out"
#echo "CREATING ES DOCUMENTS" > $outfile
#python ./ingest-publications.py --index ${indexname} --spooldir ${outdir} ${outdir}/allpubs.idx  >> $outfile 2>&1
#echo "Index counts prior to run" >> $outfile
#./idx_get_count.sh $indexname >> $outfile
curl -XDELETE localhost:9200/${indexname} >> $outfile
curl -XPUT localhost:9200/${indexname} >> $outfile
curl -XPUT localhost:9200/${indexname}/publication/_mapping?pretty --data-binary @mappings/publication.json >> $outfile
for f in $outdir/idx-*
do 
   echo $f 
   curl -XPUT 'localhost:9200/_bulk' --data-binary @$f >> $outfile 2>&1
done

sleep 10
echo "Index counts after run" >> $outfile
./idx_get_count.sh $indexname >> $outfile 2>&1
