#!/bin/bash

set -e

rm -f stashofexile.zip
cd dist/stashofexile
zip -r ../../stashofexile.zip .
cd ..
