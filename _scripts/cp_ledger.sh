SETUP_NODES="nl_genesis nl_pr1 nl_pr2 nl_pr3 nl_pr4 nl_node5" 
LEDGER="_resources/ledgers/5n4pr_bucket0-1-88-90-100_10kaccs_v24.ldb"

for i in ${SETUP_NODES}; do if [ \"${IS_ROCKS_DB}\" = true ]; then rm -rf ./nano_nodes/$i/Na
noTest/rocksdb && cp -r ${LEDGER} ./nano_nodes/$i/NanoTest/rocksdb; else cp ${LEDGER} ./nano_nodes/$i/NanoTest/data.ldb; fi; done
