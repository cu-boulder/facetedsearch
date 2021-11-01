# get counts of index prior to deletion
. ./vivoapipw.py
dstamp=`date +%Y%m%d-%H%M%S`
outdir="spool/${dstamp}"
indexname=$PEOPLEINDEX
mkdir spool/$dstamp
logfile="spool/${dstamp}/rebuild-index.out"
outputfile="fispeople.idx"
fullpathoutputfile="spool/${dstamp}/${outputfile}"
echo "CREATING ES DOCUMENTS" # > $logfile
python ./ingest-people.py --index ${indexname} --sparql ${ENDPOINT} --thread=8 $fullpathoutputfile   >> $logfile 2>&1
EXITCODE=$?
if [ $EXITCODE -ne 0 ]
then
  echo "NON ZERO EXITCODE: $EXITCODE" >>$logfile 2>&1
  cat $logfile | mailx -s "Error: rebuild-people.sh - ingest-people.py error" elsborg@colorado.edu
  exit
fi

outputsize=`wc -l $fullpathoutputfile | awk  '{print $1}'`
echo "$outputsize lines in $fullpathoutputfile"
if [ $outputsize -lt 1900 ]
then
  echo "Not enough lines in output. Amount of lines: $outputsize. File: ${outdir}/$indexname" >>$logfile 2>&1
  cat $logfile | mailx -s "Error: rebuild-people.sh - not enough lines in json output" elsborg@colorado.edu
  exit
fi

#DRE ./idx_get_count.sh ${indexname} >> $logfile
python load-data.py --spooldir ${outdir} --esendpoint ${PRODESENDPOINT} --esuser ${ESUSER} --espass ${ESPASS} --esservice ${ESSERVICE} --esregion ${ESREGION} --index ${indexname} --out $outputfile >> $logfile 2>&1
sleep 5
echo "load-data.py finished: `date +%Y%m%d-%H%M%S`" >> $logfile 2>&1
echo "Index counts after run" >> $logfile
./idx_get_count.sh >> $logfile 2>&1
