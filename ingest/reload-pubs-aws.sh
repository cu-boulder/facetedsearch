. ./vivoapipw.py
indexname=$PUBSINDEX
dstamp=`date +%Y%m%d-%H%M%S`
dstamp="20200825-164856"
outdir="spool/${dstamp}"
#mkdir $outdir
outfile="${outdir}/reload-pubs.out"
echo "Files in $outdir"
#python ./ingest-publications.py --index ${indexname} --sparql ${ENDPOINT} --spooldir ${outdir} ${outdir}/allpubs.idx  >> $outfile 2>&1
echo "Index counts prior to run" 
./idx_get_count.sh $indexname 

python ./load-data.py --spooldir ${outdir}  allpubs.idx

sleep 1
echo "Index counts after run"
./idx_get_count.sh $indexname
