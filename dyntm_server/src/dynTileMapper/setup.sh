#!/bin/bash
python setup.py sdist
cp dist/dynTileMapper-0.2.tar.gz ../../geodaWeb/trunk/ec2/packages/dist/
cd ../../geodaWeb/trunk/ec2/packages
python sync_with_s3.py
