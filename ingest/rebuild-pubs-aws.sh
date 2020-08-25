. ./vivoapipw.py
indexname=$PUBSINDEX
dstamp=`date +%Y%m%d-%H%M%S`
outdir="spool/${dstamp}"
mkdir $outdir
logfile="${outdir}/rebuild-pubs.out"
echo "CREATING ES DOCUMENTS" # > $logfile
python ./ingest-publications.py --index ${indexname} --sparql ${ENDPOINT} --threads 10 --spooldir ${outdir} allpubs.idx   >> $logfile 2>&1
EXITCODE=$?
if [ $EXITCODE -ne 0 ]
then
  echo "NON ZERO EXITCODE: $EXITCODE" >>$logfile 2>&1
  cat $logfile | mailx -s "ERROR: rebuild-pubs.sh - error in ingest-publications.py" elsborg@colorado.edu
  exit
fi

outputsize=`wc -l ${outdir}/full-allpubs.idx | awk  '{print $1}'`
echo "$outputsize lines in ${outdir}/full-allpubs.idx"
if [ $outputsize -lt 75 ]
then
  echo "Not enough lines in output. Amount of lines: $outputsize. File: ${outdir}/full-allpubs.idx" >>$logfile 2>&1
  cat $logfile | mailx -s "ERROR: rebuild-pubs.sh - not enough lines in json file" elsborg@colorado.edu
  exit
fi

./idx_get_count.sh $indexname >> $logfile
python load-data.py --spooldir ${outdir} allpubs.idx

sleep 5 
echo "Index counts after run" >> $logfile
./idx_get_count.sh $indexname >> $logfile 2>&1
