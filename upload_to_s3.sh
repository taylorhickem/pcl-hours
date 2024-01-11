#!/bin/bash

# hello

echo upload to S3 script started
GIT_REPO=${PWD##*/} 
echo $GIT_REPO
layers_full_path=$GIT_REPO/$LAYERS_PATH
echo $layers_full_path
cfn_template_full_path=$GIT_REPO/$CFN_TEMPLATE_PATH
echo $cfn_template_full_path

mkdir remote_files
cd remote_files

echo listing files in s3://$S3_BUCKET/git
aws s3 ls s3://$S3_BUCKET/git --recursive

#echo downloading from s3://$S3_BUCKET/git/$layers_full_path
#aws s3 cp s3://$S3_BUCKET/git/$layers_full_path layers.json

#echo downloading from s3://$S3_BUCKET/git/$cfn_template_full_path
#aws s3 cp s3://$S3_BUCKET/git/$cfn_template_full_path cfn_template.yaml

ls

cd ..
rm -r remote_files
