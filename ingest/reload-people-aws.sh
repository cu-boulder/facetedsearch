# get counts of index prior to deletion
. ./vivoapipw.py
dstamp=20220723-091601
outdir="spool/${dstamp}"
indexname=$PEOPLEINDEX
#mkdir spool/$dstamp
outputfile="fispeople"
logfile="spool/${dstamp}/rebuild-index.out"
echo "CREATING ES DOCUMENTS" # > $logfile
#./idx_get_count.sh ${indexname} #>> $logfile
python3 load-data.py --spooldir ${outdir} --esendpoint ${PRODESENDPOINT} --esuser ${ESUSER} --espass ${ESPASS} --esservice ${ESSERVICE} --esregion ${ESREGION} --index ${indexname} --out $outputfile #DRE >> $logfile 2>&1
sleep 10
echo "Index counts after run" #>> $logfile
./idx_get_count.sh #>> $logfile 2>&1
