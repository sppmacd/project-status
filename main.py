#!/usr/bin/env python3
import os
import sys
import time

from ps.files import *
from ps.util import *
        
def main():
    FileDescriptorManager()
    
    fileList = Directory(".")
    print(fileList)
    print(len(FileDescriptorManager.instance.descriptors))

if __name__ == "__main__":
    main()
else:
    print("Importing not supported")
