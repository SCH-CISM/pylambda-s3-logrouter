#!/bin/bash
rm -rf vendored
rm -rf ../s3_logrouter.zip
mkdir -p vendored
pip install -r requirements.txt -t ./vendored
zip -X -r ../s3_logrouter.zip s3_logrouter.py
cd vendored
zip -X -r ../../s3_logrouter.zip ./
cd -
