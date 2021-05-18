#!/usr/bin/env python3
import os

import util

class File:
    def __init__(self, path):
        self.path = path
        
    def __str__(self, depth=0):
        return util.depth_indent(depth) + self.path + "\n"

class Directory(File):
    def __init__(self, path):
        File.__init__(self, path)
        self.files = {}
        for file in os.listdir(path):
            if os.path.isdir(file):
                self.files[file] = Directory(path + "/" + file)
            else:
                self.files[file] = File(path + "/" + file)
            
    def __str__(self, depth=0):
        out = File.__str__(self, depth)
        for value in self.files.values():
            out = out + value.__str__(depth + 1)
        return out
        
fileList = Directory(".")
print(fileList)
        
