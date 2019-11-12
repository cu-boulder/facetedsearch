# get counts of index prior to deletion
. ./vivoapipw.py
dstamp=`date +%Y%m%d-%H%M%S`
indexname=$PEOPLEINDEX
mkdir spool/$dstamp
logfile="spool/${dstamp}/rebuild-index.out"
outputfile="spool/${dstamp}/people.list"
echo "CREATING ES DOCUMENTS" # > $logfile
python ./ingest-people.py --index ${indexname} --sparql ${ENDPOINT} --thread=8 $outputfile   >> $logfile 2>&1
EXITCODE=$?
if [ $EXITCODE -ne 0 ]
then
  echo "NON ZERO EXITCODE: $EXITCODE" >>$logfile 2>&1
  cat $logfile | mailx -s "Error: rebuild-people.sh - ingest-people.py error" elsborg@colorado.edu
  exit
fi

outputsize=`wc -l $outputfile | awk  '{print $1}'`
echo "$outputsize lines in $outputfile"
if [ $outputsize -lt 1900 ]
then
  echo "Not enough lines in output. Amount of lines: $outputsize. File: ${outdir}/allpubs.idx" >>$logfile 2>&1
  cat $logfile | mailx -s "Error: rebuild-people.sh - not enough lines in json output" elsborg@colorado.edu
  exit
fi

./idx_get_count.sh ${indexname} >> $logfile
curl -XDELETE localhost:9200/${indexname} >> $logfile
curl -XPUT localhost:9200/${indexname} >> $logfile
#curl -XPUT -H 'Content-Type: application/json' localhost:9200/${indexname}/person/_mapping?pretty --data-binary @mappings/person.json #>> $logfile
curl -XPOST -H 'Content-Type: application/json' localhost:9200/_bulk --data-binary @$outputfile >> $logfile 2>&1
sleep 10
echo "Index counts after run" >> $logfile
./idx_get_count.sh >> $logfile 2>&1
