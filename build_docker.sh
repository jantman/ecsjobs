#!/bin/bash

source bin/activate
set +x
IMGNAME="jantman/ecsjobs:$(date +%s)"
rm -Rf dist/*
python setup.py bdist_wheel
WHLNAME=$(basename dist/ecsjobs*.whl)
docker build -t $IMGNAME \
  --build-arg git_url=$(git config remote.origin.url) \
  --build-arg git_commit=$(git rev-parse --short HEAD) \
  --build-arg build_time=$(date +%s) \
  --build-arg whlname=$WHLNAME \
  .
echo "Built: $IMGNAME"
