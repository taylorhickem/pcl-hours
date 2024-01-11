#!/bin/bash

# hello

echo upload to S3 script started
git diff --name-status $CODEBUILD_WEBHOOK_BASE_REF
