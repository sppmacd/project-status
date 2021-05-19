import os

from .detector import DetectorRegistry
from .guessers import FileType
from .logging import *
from .util import *

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
        print_verbose("open_and_push_file " + path)
        if len(self.descriptor_queue) + 1 > self.maxfds:
            fd = self.descriptor_queue[0]
            print_verbose("too much fds opened, removing " + str(fd))
            oldpath = fd.name
            fd.close()
            del self.descriptor_queue[0]
            del self.descriptors[oldpath]

        try:
            fd = open(path)
            self.descriptor_queue.append(fd)
            self.descriptors[path] = len(self.descriptor_queue)
            return fd
        except OSError:
            excinfo = sys.exc_info()[1]
            print_error("Failed to open file " + excinfo.filename + ": " + excinfo.strerror)

class File:
    def __init__(self, parent, path):
        self.path = path
        self.parent = parent
        self.basename = os.path.basename(path)
        self.extension = os.path.splitext(path)[1]
        self.type_guesses = None
        
    def __str__(self, depth=0):
        return depth_indent(depth) + sgr("33", self.path) + sgr("90", " -> ") + str(self.file_type()) + "\n"
    
    def is_directory(self):
        return False
    
    def file_type(self):
        if self.type_guesses == None:
            self.type_guesses = DetectorRegistry.instance.guess_file_type(self)
        return self.type_guesses
    
    def is_special(self):
        for guess in self.file_type():
            if guess.is_special():
                return True
        return False
    
    def descriptor(self):
        if self.is_directory():
            return None
        else:
            return FileDescriptorManager.instance.get_by_path(self.path)

class Directory(File):
    def __init__(self, parent, path):
        print_verbose(path)
        File.__init__(self, parent, path)
        self.files = {}
        self.m_is_project = None
        
        if not self.should_traverse_into():
            print_verbose("Special path: " + path)
            return
        
        try:
            for file in os.listdir(path):
                if os.path.isdir(path + "/" + file):
                    self.files[file] = Directory(self, path + "/" + file)
                else:
                    self.files[file] = File(self, path + "/" + file)
        except OSError:
            excinfo = sys.exc_info()[1]
            print_error("Failed to open file " + excinfo.filename + ": " + excinfo.strerror)
            
    def __str__(self, depth=0):
        out = File.__str__(self, depth)
        out = out[:-1]
        out += (sgr("1;32", " (IS LIKELY A PROJECT)\n") if self.is_project() else "\n")
        for value in self.files.values():
            out = out + value.__str__(depth + 1)
        return out
    
    def is_directory(self):
        return True
    
    def is_project(self):
        print_verbose("is_project " + self.path)
        if self.m_is_project == None:
            if self.parent != None and self.parent.is_project():
                print_verbose("nested project") # Don't allow nested projects for now.
                self.m_is_project = False
                return self.m_is_project 
            
            has_non_mimetype_guess = False
            for file in self.files.values():
                for guess in file.file_type():
                    if guess.file_type.clazz != FileType.Class.MimeType:
                        has_non_mimetype_guess = True
                
            self.m_is_project = has_non_mimetype_guess
        return self.m_is_project
        
    def should_traverse_into(self):
        return not self.is_special()
