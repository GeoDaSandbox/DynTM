#!/bin/bash
python setup.py sdist
rm MANIFEST
cp dist/gws-0.0.6.tar.gz ../../ec2/packages/dist/
cd ../../ec2/packages
python sync_with_s3.py
