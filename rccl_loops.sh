#!/bin/bash
# test loops
LOOPS=20

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
echo "Start test time:" `date '+%Y%m%d_%H%M%S'` |tee -a $LOG	
START=$(date '+%s')
#cmd=`find /root -name rocm_bandwidth_test |grep "rocm_bandwidth_test/rocm_bandwidth_test"`
#cmd="HIP_VISIBLE_DEVICES=4,5,6,7 HSA_NO_SCRATCH_RECLAIM=1 NCCL_DEBUG=INFO NCCL_MIN_NCHANNELS=12 /root/test/rccl-tests/build/all_reduce_perf -b 128M -e 2048M -f 2 -g 4"
echo "Test command:" $cmd  |tee -a $LOG
for ((i=1;i<=$LOOPS;i++));do
    echo "==================" |tee -a $LOG
    echo "Test cycle(s) " $i |tee -a $LOG
	echo "==================" |tee -a $LOG
    /root/test/rccl-tests/build/all_reduce_perf -b 128M -e 2048M -f 2 -g 4 |tee -a $LOG
	if [ $? -eq 0 ]; then
        echo "Cycle(s) "$i "rccl test passed" |tee -a $LOG
    else
        echo "Cycle(s) "$i "rccl test failed" |tee -a $LOG
    fi	
done
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

