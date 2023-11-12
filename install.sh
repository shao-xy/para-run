#!/bin/bash

# if test $(id -u) -ne 0; then
# 	echo "Fatal: Must be ROOT to execute this script."
# 	exit 0
# fi
# 
# python3 setup.py install

source build.sh
pip3 install dist/*.whl
