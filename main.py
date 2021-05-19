#!/usr/bin/env python3
import os
import sys
import time

from ps.detector import DetectorRegistry
from ps.files import Directory, FileDescriptorManager
from ps.logging import *
        
def main():
    FileDescriptorManager()
    
    file_list = Directory(".")
    print(file_list)

if __name__ == "__main__":
    main()
else:
    print_error(sgr("31", "Importing as module not supported!"))
