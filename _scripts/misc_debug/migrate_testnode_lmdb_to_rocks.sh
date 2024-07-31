#Put this at the root of a local nano_node to migrate form lmdb to rocksdb

export NANO_TEST_GENESIS_BLOCK='{"account": "nano_1fzwxb8tkmrp8o66xz7tcx65rm57bxdmpitw39ecomiwpjh89zxj33juzt6p", "representative": "nano_1fzwxb8tkmrp8o66xz7tcx65rm57bxdmpitw39ecomiwpjh89zxj33juzt6p", "source": "37FCEA4DA94F1635484EFCBA57483C4C654F573B435C09D8AACE1CB45E63FFB1", "signature": "492FBB6A8852FD6086739D151454A5A6A2920D9A6085FDA1F00690D46D9AEC7668A75ECCAA4F52220859E1F45558500A32735060E8B1D0611079B62751457A05", "work": "6d7d8e388d9c853f", "type": "open"}'
export NANO_TEST_GENESIS_PUB=37FCEA4DA94F1635484EFCBA57483C4C654F573B435C09D8AACE1CB45E63FFB1
export NANO_TEST_EPOCH_1=0x000000000000000f
export NANO_TEST_EPOCH_2=0x000000000000000f
export NANO_TEST_EPOCH_2_RECV=0x000000000000000f
export NANO_TEST_MAGIC_NUMBER=RX
export NANO_TEST_CANARY_PUB=CCAB949948224D6B33ACE0E078F7B2D3F4D79DF945E46915C5300DAEF237934E

./nano_node --network=test --data_path=./NanoTest/ --migrate_database_lmdb_to_rocksdb