#!/usr/bin/env python3
import os
import sys
import time

from ps.detector import DetectorRegistry
from ps.files import Directory, FileDescriptorManager
        
def main():
    FileDescriptorManager()
    
    file_list = Directory(".")
    print(file_list)
    print(len(FileDescriptorManager.instance.descriptors))

if __name__ == "__main__":
    main()
else:
    print("Importing not supported")
