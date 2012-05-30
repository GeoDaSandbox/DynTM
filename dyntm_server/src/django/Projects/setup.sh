#!/bin/bash

# Creates a tar ball that should be extracted to /usr/local/django

mkdir django
svn export gws_sqlite django/gws_sqlite
svn export wsgi django/wsgi
tar cfvz gws_project.tar.gz django
rm -rf django
mv gws_project.tar.gz ../../ec2/packages/dist/
cd ../../ec2/packages
python sync_with_s3.py



