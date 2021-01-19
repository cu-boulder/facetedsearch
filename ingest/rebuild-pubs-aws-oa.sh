. ./vivoapipw.py
indexname=$PUBSOAINDEX
dstamp=`date +%Y%m%d-%H%M%S`
outdir="spool/${dstamp}"
mkdir $outdir
logfile="${outdir}/rebuild-pubs.out"
echo "CREATING ES DOCUMENTS"  > $logfile
echo "Starttime: $dstamp" >> $logfile
echo $MINPUBSCOUNT >> $logfile
python ./ingest-publications-oa.py --index ${indexname} --sparql ${ENDPOINT} --threads 10 --spooldir ${outdir} allpubs.idx   >> $logfile 2>&1
EXITCODE=$?
if [ $EXITCODE -ne 0 ]
then
  echo "NON ZERO EXITCODE: $EXITCODE" >> $logfile 2>&1
  cat $logfile | mailx -s "ERROR: rebuild-pubs.sh - error in ingest-publications.py" $NOTIFYEMAIL
  exit
fi
echo "Ingest-publications finished: `date +%Y%m%d-%H%M%S`" >> $logfile 2>&1

outputsize=`wc -l ${outdir}/full-allpubs.idx | awk  '{print $1}'`
echo "$outputsize lines in ${outdir}/full-allpubs.idx" >> $logfile
if [ $outputsize -lt $MINPUBSCOUNT ]
then
  echo "Not enough lines in output. Amount of lines: $outputsize. File: ${outdir}/full-allpubs.idx" >>$logfile 2>&1
  cat $logfile | mailx -s "ERROR: rebuild-pubs.sh - not enough lines in json file" $NOTIFYEMAIL
  exit
fi

./idx_get_count.sh $indexname >> $logfile
python load-data.py --spooldir ${outdir} --esendpoint ${ESENDPOINT} --esservice ${ESSERVICE} --esregion ${ESREGION} --index ${indexname} allpubs.idx >> $logfile 2>&1

sleep 5 
echo "load-data.py finished: `date +%Y%m%d-%H%M%S`" >> $logfile 2>&1
echo "Index counts after run" >> $logfile
./idx_get_count.sh $indexname >> $logfile 2>&1
