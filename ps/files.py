import copy
import fnmatch
import os

import config as config
from .detector import DetectorRegistry
from .guessers import FileType, FileGuess
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
            fd = open(path, mode="rb")
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
        
    def __str__(self, depth=0, **kwargs):
        return depth_indent(depth) + sgr("33", self.path) + sgr("90", " -> ") + str(self.collapsed_guesses()) + "\n"
    
    def is_directory(self):
        return False
    
    def guesses(self):
        if self.type_guesses == None:
            self.type_guesses = self.generate_guesses()
        return self.type_guesses
    
    def collapsed_guesses(self):
        return self.guesses()
    
    def generate_guesses(self):
        return DetectorRegistry.instance.guess_file_type(self)
    
    def is_special(self):
        for guess in self.guesses():
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
        self.collapsed_type_guesses = []
        
        if not self.should_traverse_into():
            print_verbose("Special path: " + path)
            return
        
        try:
            for file in os.listdir(path):
                isdir = os.path.isdir(path + "/" + file)
                if self.should_be_excluded(file, isdir):
                    continue
                
                if isdir:
                    self.files[file] = Directory(self, path + "/" + file)
                else:
                    self.files[file] = File(self, path + "/" + file)
        except OSError:
            excinfo = sys.exc_info()[1]
            print_error("Failed to open file " + excinfo.filename + ": " + excinfo.strerror)
            
        # "Collapse" attributes.
        if parent == None:
            self.collapsed_type_guesses = self.generate_collapsed_guesses()
            
    def __str__(self, depth=0, **kwargs):
        out = File.__str__(self, depth)
        out = out[:-1]
        out += (sgr("1;32", " (IS A PROJECT)\n") if self.should_display_as_project() else "\n")
        for value in self.files.values():
            if len(value.guesses()) > 0:
                out = out + value.__str__(depth + 1)
        return out
    
    def is_directory(self):
        return True
    
    def is_project(self):
        has_non_mimetype_guess = False
        for file in self.files.values():
            for guess in file.collapsed_guesses():
                if guess.file_type.clazz != FileType.Class.MimeType:
                    has_non_mimetype_guess = True
            
        m_is_project = has_non_mimetype_guess
        return m_is_project
    
    def should_display_as_project(self):
        if self.parent != None and self.parent.is_project():
            # Don't allow nested projects for now.
            return False
        
        return self.is_project()
    
    def collapsed_guesses(self):
        if self.collapsed_type_guesses == []:
            self.collapsed_type_guesses = self.generate_collapsed_guesses()
        return self.collapsed_type_guesses
    
    def generate_collapsed_guesses(self):
        if self.collapsed_type_guesses != []:
            raise AssertionError("Collapsed guesses generated double")
        
        guesses = DetectorRegistry.instance.guess_file_type(self)
        
        # FIXME: O(n^3) complexity?
        for file in self.files.values():
            for other_guess in file.collapsed_guesses():
                done = False
                
                # Find matching guess
                guess = None
                for my_guess in guesses:
                    if my_guess.file_type.clazz == other_guess.file_type.clazz and my_guess.file_type.value == other_guess.file_type.value:
                        guess = my_guess
                
                # If guess matches, collapse attributes
                if guess != None:
                    for name, value in other_guess.attributes.items():
                        guess.collapse_attribute(name, value)
                # Else, create a new guess
                else:
                    guess = FileGuess(other_guess.file_type)
                    guess.guesser = other_guess.guesser
                    guesses.append(guess)
                    
                    # Try to collapse attributes
                    for name, value in other_guess.attributes.items():
                        guess.collapse_attribute(name, value)

        return guesses
    
    def print_as_project(self):
        print(sgr("1;34", self.path))
        for guess in self.collapsed_guesses():
            print(" •", guess.to_user_readable_string())
    
    def print_projects(self):
        if self.should_display_as_project():
            self.print_as_project()
        for file in self.files.values():
            if file.is_directory():
                file.print_projects()
        
    def should_traverse_into(self):
        return not self.is_special()
    
    def should_be_excluded(self, filename, isdir):
        for exclude_pattern in config.args.exclude:
            if len(exclude_pattern) > 0 and not exclude_pattern.startswith("/") and fnmatch.fnmatch(filename, exclude_pattern):
                return True
        if len(config.args.include) > 0 and not isdir:
            non_guesser_count = 0
            for include_pattern in config.args.include:
                if not include_pattern.startswith("/"):
                    non_guesser_count += 1
                    if len(include_pattern) > 0 and fnmatch.fnmatch(filename, include_pattern):
                        return False
            return non_guesser_count > 0
        return False
