#!/bin/bash
# test loops

LOOPS=5

# define and create log path
project_path=$(cd `dirname $0`; pwd)
base_name=`basename $0`
NAME=`echo $base_name|awk -F ".sh" '{print $1}'`
FULLPATH=${project_path}"/log_"${NAME}
if [ ! -d $FULLPATH ]; then
    mkdir $FULLPATH
fi	

# PM log duration and path
PMLOG_DURATION=1000
TIMESTAMP=$(date '+%Y%m%d_%H%M%S')
PMLOG=$FULLPATH"/pm_"$CASENAME"_"$TIMESTAMP".csv"

#test logs
LOG=$FULLPATH"/"$NAME"_"$TIMESTAMP".log"
XGMILINK_LOG=$FULLPATH"/xgmilinkstatus_"$TIMESTAMP".log"
PCIELINK_LOG=$FULLPATH"/pcielinkstatus_"$TIMESTAMP".log"
SDR_LOG=$FULLPATH"/sdr_"$TIMESTAMP".log"
DMESG_LOG=$FULLPATH"/dmesg_"$TIMESTAMP".log"

# create get_sdr.sh 
echo "#!/bin/bash" >get_sdr.sh
echo "while (true)" >>get_sdr.sh
echo "do" >>get_sdr.sh
echo "ipmitool sdr >>"$SDR_LOG >>get_sdr.sh
echo "sleep 10" >>get_sdr.sh
echo "done" >>get_sdr.sh
chmod +x get_sdr.sh

# Start record logs
echo "Test start ..." >$XGMILINK_LOG
echo "Test start ..." >$PCIELINK_LOG
/root/tools/atitool/atitool -xgmilinkstatus >>$XGMILINK_LOG
lspci -d 1002: -vvv >>$PCIELINK_LOG
./get_sdr.sh &
dmesg -C



# Get linux kernel
echo "Linux Kernal:" |tee -a $LOG
uname -a |tee -a $LOG
echo "------------------------------------------------" |tee -a $LOG

# Get compute packages
echo "Compute Packages:" |tee -a $LOG
dpkg -l | grep 'rocm\|rocr\|roct\|hsa\|hcc\|hip_\|compute_roc' |tee -a $LOG
echo ""
echo "------------------------------------------------" |tee -a $LOG



echo "Launching pmlogs ... "
(( ${PMLOG_DURATION} > 0 )) && ATITOOL_PIDS=$(python2 -c "import os, atitool_lib; atitool_lib.run_atitool('$PMLOG','${PMLOG_DURATION}')")

echo "------------------------------------------------" |tee -a $LOG
python docker_c2.py |tee -a $LOG

echo "End test time:" `date '+%Y%m%d_%H%M%S'` |tee -a $LOG	
echo "duration $(($(date '+%s')-START)) seconds" | tee -a $LOG

echo "Cleaning up ..."
(( ${PMLOG_DURATION} > 0 )) && kill ${ATITOOL_PIDS} 2> /dev/null
# End logs
echo "Test End ..." >>$XGMILINK_LOG
echo "Test End ..." >>$PCIELINK_LOG
/root/tools/atitool/atitool -xgmilinkstatus >>$XGMILINK_LOG
lspci -d 1002: -vvv >>$PCIELINK_LOG
killall get_sdr.sh
dmesg >$DMESG_LOG
reset

