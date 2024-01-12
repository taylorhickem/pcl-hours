#!/bin/bash

# hello

echo upload to S3 script started
remote_dir=remote
GIT_REPO=${PWD##*/}
ACTION_TYPES=function_update
echo GIT_REPO $GIT_REPO
echo LAYERS_PATH $LAYERS_PATH
echo CFN_TEMPLATE_PATH $CFN_TEMPLATE_PATH

mkdir remote_files

file_compare layers_update $LAYERS_PATH layers.json
file_compare stack_update $CFN_TEMPLATE_PATH cfn_template.yaml

rm -r remote_files

ACTION_TYPES=[$ACTION_TYPES]
echo ACTION_TYPES $ACTION_TYPES

file_compare () {
  endpoint=s3://$S3_BUCKET/git/$GIT_REPO/$2
  aws s3 cp $endpoint $remote_dir/$3
  if [ $? == 0 ]
    if [ "$(cat $2)" != "$(cat $remote_dir/$3)" ] then
      ACTION_TYPES=$ACTION_TYPES,$1
  else
    echo $3 not found at $endpoint
}