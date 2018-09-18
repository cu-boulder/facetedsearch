# get counts of index prior to deletion
indexname=webex-v2
dstamp=`date +%Y%m%d-%H%M%S`
outdir="spool/${dstamp}"
mkdir $outdir
outfile="${outdir}/rebuild-webex.out"
echo "CREATING ES DOCUMENTS" > $outfile
python ./ingest-publications.py --index ${indexname} --spooldir ${outdir} ${outdir}/${indexname}.idx  >> $outfile 2>&1
echo "Index counts prior to run" >> $outfile
./idx_get_count.sh $indexname >> $outfile
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
python get_index_status.py
