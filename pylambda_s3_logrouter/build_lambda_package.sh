#!/bin/bash

deactivate

# clean
rm -rf vendored
rm -rf ../s3_logrouter.zip
rm -rf venv

virtualenv venv
source ./venv/bin/activate
mkdir -p vendored
pip install -r requirements.txt
pip install -r requirements.txt -t ./vendored
zip -X -r ../s3_logrouter.zip s3_logrouter.py
zip -X -r ../s3_logrouter.zip config.yml
cd vendored
zip -X -r ../../s3_logrouter.zip ./
cd -
cd venv/lib/python2.7/site-packages
zip -X -r  ../../../../../s3_logrouter.zip ./
cd -
