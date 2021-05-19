#!/usr/bin/env python3
import argparse
import os
import sys
import time

from ps.detector import DetectorRegistry
from ps.files import Directory, FileDescriptorManager
import ps.logging

def parse_args():
    parser = argparse.ArgumentParser(description="Manage your projects.")
    parser.add_argument("path", nargs="?", help="Path to scan", default=".")
    parser.add_argument("--disable-formatting", help="Disable output formatting", action="store_true")
    parser.add_argument("--display-tree", "-t", help="[action] Display filesystem tree", action="store_true")
    parser.add_argument("--verbose", "-v", help="Print what is done", action="store_true")
    
    return parser.parse_args()

def main(args):
    ps.logging.user_disable_formatting = args.disable_formatting
    ps.logging.user_verbose = args.verbose
    
    FileDescriptorManager()
    
    something_will_be_done = args.display_tree
    if not something_will_be_done:
        ps.logging.print_error("You must specify action!")
        sys.exit(1)
    
    file_list = Directory(args.path)
    
    if args.display_tree:
        print(file_list)

if __name__ == "__main__":
    main(parse_args())
else:
    print_error(ps.logging.sgr("31", "Importing as module not supported!"))
