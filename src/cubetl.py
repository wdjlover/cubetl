#!/usr/bin/python

import os

from cubetl.core.bootstrap import Bootstrap
import sys

def main():
    
    bootstrap = Bootstrap()
    bootstrap.start(sys.argv[1:])

if __name__ == "__main__":
    main()

