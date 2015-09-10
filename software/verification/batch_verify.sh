#!/bin/bash

# This script searches for scans that match the given exp/obs/scan 
# search strings, and for each matched item calls verify_scan.py on 
# that scan. Matches are found against single dish data files, so use
# "Sn" for the station code.
if [ "$#" -lt 3 ] ; then
	echo "Usage: $0 EXP OBS SCAN" >&2
	exit 1
fi

EXP=$1
OBS=$2
SCAN=$3

EXEC="./verify_scan.py"
ARGS="-c 32 -v 1"
BATCH_LOG="./out/batch_verify.log"

echo "Batch started `date`" >> $BATCH_LOG
echo "====================" >> $BATCH_LOG

PATH_SINGLE_DISH=/home/ayoung/Work/obs/March2015/single-dish-data
SEARCH_STR=`echo "${PATH_SINGLE_DISH}/${EXP}_${OBS}_${SCAN}.vdif"`
for f in `ls $SEARCH_STR` ; do
	FILENAME=`echo $f | grep -E -o "[^[:space:]/]*.vdif"`
	PARTS=`echo $FILENAME | sed y/\_/\ / | sed s/".vdif"// | sed s/Sn/Sm/`
	if $EXEC $ARGS $PARTS ; then 
		echo "SUCCESS ($FILENAME)" >> $BATCH_LOG
	else
		echo "FAILURE ($FILENAME)" >> $BATCH_LOG
	fi
done