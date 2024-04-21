## Install gcloud dependecy and setup virtual python environment

```bash
./install_gcloud.sh #installs gcloud dependencies
./init_gcloud_venv.sh #installs a virtial python env
nano config_gcloud.json # modify config settings
```


- gcloud_nano.py : creates glcoud instances for each node in
  - requires gcloud_dc.yml (docker-compose file)
  - requires script_set_worker_ledger.sh (downloads the ledger files and starts docker compose. )
- update_config.py : modifies the config created by nanomock so it can be used to publish block via rpc url
- gcluster.py : mangae instances (list, restart, delete)