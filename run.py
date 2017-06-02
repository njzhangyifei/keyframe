#!/usr/bin/python3

import sys
import os

py_path = (os.path.dirname(os.path.realpath(__file__)))
sys.path += [py_path]

if __name__ == '__main__':
    from sfmkeyframe import app
