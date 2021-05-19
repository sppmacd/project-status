#!/usr/bin/env python3
import os
import sys
import time

import util

class FileDescriptorManager:
    instance = None
    
    def __init__(self, maxfds=8):
        if FileDescriptorManager.instance == None:
            FileDescriptorManager.instance = self
        else:
            raise AssertionError("Double singleton")
        
        self.descriptor_queue = []
        self.descriptors = {}
        self.maxfds = maxfds
    
    def get_by_path(self, path):
        # Pop from current position and move to front of queue
        
        fd = self.descriptors.get(path)
        if not fd in self.descriptor_queue:
            return self.open_and_push_file(path)
        else:
            self.descriptor_queue.remove(fd)
            self.descriptor_queue.append(fd)
            return fd
            
    def open_and_push_file(self, path):
        print("open_and_push_file " + path)
        if len(self.descriptor_queue) + 1 > self.maxfds:
            fd = self.descriptor_queue[0]
            print("too much fds opened, removing ", fd)
            oldpath = fd.name
            fd.close()
            del self.descriptor_queue[0]
            del self.descriptors[oldpath]
            print(self.descriptor_queue)

        try:
            fd = open(path)
            self.descriptor_queue.append(fd)
            self.descriptors[path] = len(self.descriptor_queue)
            return fd
        except PermissionError:
            excinfo = sys.exc_info()[1]
            print("Failed to open file " + excinfo.filename + ": " + excinfo.strerror)
        except:
            excinfo = sys.exc_info()[1]
            raise AssertionError("Failed to open file " + excinfo.filename + ": " + excinfo.strerror)

class File:
    def __init__(self, path):
        self.path = path
        
    def __str__(self, depth=0):
        fd = self.descriptor()
        return util.depth_indent(depth) + self.path + ": " + str(fd.closed if fd else None) + "\n"
    
    def is_directory(self):
        return False
    
    def descriptor(self):
        if self.is_directory():
            return None
        else:
            return FileDescriptorManager.instance.get_by_path(self.path)

class Directory(File):
    def __init__(self, path):
        File.__init__(self, path)
        self.files = {}
        for file in os.listdir(path):
            if os.path.isdir(path + "/" + file):
                self.files[file] = Directory(path + "/" + file)
            else:
                self.files[file] = File(path + "/" + file)
            
    def __str__(self, depth=0):
        out = File.__str__(self, depth)
        for value in self.files.values():
            out = out + value.__str__(depth + 1)
        return out
    
    def is_directory(self):
        return True
        
def main():
    FileDescriptorManager()
    
    fileList = Directory(".")
    print(fileList)
    print(len(FileDescriptorManager.instance.descriptors))

if __name__ == "__main__":
    main()
else:
    print("Importing not supported")
