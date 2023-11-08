#!/bin/bash

if test $(id -u) -ne 0; then
	echo "Fatal: Must be ROOT to execute this script."
	exit 0
fi

test -d build/ && rm -rf build
test -d dist/ && rm -rf dist
test -d *.egg-info && rm -rf *.egg-info/

python3 setup.py install
