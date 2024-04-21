#!/bin/sh

#Script to create and delete a virtualenv to keep dependencies separate from other projects
# ./gcloud_venv.sh create
 # ./gcloud_venv.sh delete

action=$1

if [ "$action" = "" ];
then
    rm -rf gcloud_venv
    python3 -m venv gcloud_venv
    . gcloud_venv/bin/activate

    ./gcloud_venv/bin/pip3 install wheel
    ./gcloud_venv/bin/pip3 install -r ./gcloud/requirements.txt --quiet

    echo "update submodules"
    git submodule update --init --recursive

    echo "A new virstaul environment was created. "


elif [ "$action" = "delete" ];
then
    . gcloud_venv/bin/activate
    deactivate
    rm -rf gcloud_venv

else
     echo "run ./setup_python_venv.sh  to create a virtual python environment"
     echo "or"
     echo "run ./setup_python_venv.sh delete  to delete the virstual python environment"
fi


