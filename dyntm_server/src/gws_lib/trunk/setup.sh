#!/bin/bash
rm MANIFEST
python setup.py sdist
cp dist/gws_lib-0.0.2.tar.gz ../../trunk/ec2/packages/dist/
cd ../../trunk/ec2/packages
python sync_with_s3.py
