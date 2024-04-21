cd /mnt/nvme0n1/Crypto/Nano/projects/nanolab_testdir/nanolab_testdir_2/tracing_to_sql && 
rm -f *.log &&
./mv_logs.sh -x &&
./log2db.py && 
python3 index_adder.py capture.db &&
rm *.log && 
rm *.txt
