rm -f capture.db &&
rm -f *.log && 
rm -f *.txt &&
./mv_logs.sh -x &&
./log2db.py && 
python3 index_adder_v2.py capture.db

