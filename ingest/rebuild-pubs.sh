. ./vivoapipw.py
indexname=$PUBSINDEX
dstamp=`date +%Y%m%d-%H%M%S`
outdir="spool/${dstamp}"
mkdir $outdir
logfile="${outdir}/rebuild-pubs.out"
echo "CREATING ES DOCUMENTS" # > $logfile
python ./ingest-publications.py --index ${indexname} --sparql ${ENDPOINT} --threads 10 --spooldir ${outdir} ${outdir}/allpubs.idx   >> $logfile 2>&1
EXITCODE=$?
if [ $EXITCODE -ne 0 ]
then
  echo "NON ZERO EXITCODE: $EXITCODE" >>$logfile 2>&1
  cat $logfile | mailx -s "ERROR: rebuild-pubs.sh - error in ingest-publications.py" elsborg@colorado.edu
  exit
fi

outputsize=`wc -l ${outdir}/allpubs.idx | awk  '{print $1}'`
echo "$outputsize lines in ${outdir}/allpubs.idx"
if [ $outputsize -lt 50 ]
then
  echo "Not enough lines in output. Amount of lines: $outputsize. File: ${outdir}/allpubs.idx" >>$logfile 2>&1
  cat $logfile | mailx -s "ERROR: rebuild-pubs.sh - not enough lines in json file" elsborg@colorado.edu
  exit
fi

echo "Index counts prior to run" >> $logfile
./idx_get_count.sh $indexname >> $logfile
curl -XDELETE localhost:9200/${indexname} >> $logfile
curl -XPUT localhost:9200/${indexname} >> $logfile
curl -XPUT -H 'Content-Type: application/json' localhost:9200/${indexname}/publication/_mapping?pretty --data-binary @mappings/publication.json >> $logfile
for f in $outdir/idx-*
do 
   echo $f 
   curl -XPUT -H 'Content-Type: application/json' 'localhost:9200/_bulk' --data-binary @$f >> $logfile 2>&1
done

sleep 10
echo "Index counts after run" >> $logfile
./idx_get_count.sh $indexname >> $logfile 2>&1
