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
  cat $logfile | mailx -s "ERROR: rebuild-pubs.sh - error in ingest-publications.py" $NOTIFYEMAIL
  exit
fi

outputsize=`wc -l ${outdir}/full-allpubs.idx | awk  '{print $1}'`
echo "$outputsize lines in ${outdir}/full-allpubs.idx"
if [ $outputsize -lt $MINPUBSCOUNT ]
then
  echo "Not enough lines in output. Amount of lines: $outputsize. File: ${outdir}/full-allpubs.idx" >>$logfile 2>&1
  cat $logfile | mailx -s "ERROR: rebuild-pubs.sh - not enough lines in json file" $NOTIFYEMAIL
  exit
fi

echo "Index counts prior to run" >> $logfile
./idx_get_count.sh $indexname >> $logfile
sleep 1
echo " " >> $logfile
echo -e "\nDeleting Old Index: ${indexname}" >> $logfile
curl -XDELETE localhost:9200/${indexname} >> $logfile 2>&1
sleep 1
echo "" >> $logfile
echo -e "\nCreating new Index: ${indexname}" >> $logfile
curl -XPUT localhost:9200/${indexname} >> $logfile
sleep 1
# Don't need mapping for now
#echo " " >> $logfile
#echo -e "\nAdding mapping to Index: ${indexname}" >> $logfile
#curl -XPUT -H 'Content-Type: application/json' localhost:9200/${indexname}/publication/_mapping?pretty --data-binary @mappings/publication.json >> $logfile
#sleep 1
echo " " >> $logfile
echo -e "\nUploading bulk files to Index: ${indexname}" >> $logfile
for f in $outdir/allpubs.idx*
do 
   echo "" >> $logfile
   echo -e "\nLoading file: $f" >> $logfile 
   curl -XPUT -H 'Content-Type: application/json' 'localhost:9200/_bulk' --data-binary @$f >> $logfile 2>&1
   sleep 1
done
echo "" >> $logfile
echo "Index counts after run" >> $logfile
./idx_get_count.sh $indexname >> $logfile 2>&1
