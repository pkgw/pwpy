#! /bin/bash

. common.sh

./scan-night.py $raw/$rawglob |tee index.tab
