# get counts of index prior to deletion
. /data/vivo/virtual_environments/python3/bin/activate
. ./vivoapipw.py
dstamp=20220928-124201
outdir="spool/${dstamp}"
indexname=$PEOPLEINDEX
#mkdir spool/$dstamp
outputfile="fispeople"
logfile="spool/${dstamp}/rebuild-index.out"
echo "CREATING ES DOCUMENTS" # > $logfile
#./idx_get_count.sh ${indexname} #>> $logfile
python load-data.py --spooldir ${outdir} --esendpoint ${PRODESENDPOINT} --esuser ${ESUSER} --espass ${ESPASS} --esservice ${ESSERVICE} --esregion ${ESREGION} --index ${indexname} --out $outputfile #DRE >> $logfile 2>&1
sleep 10
echo "Index counts after run" #>> $logfile
./idx_get_count.sh #>> $logfile 2>&1
