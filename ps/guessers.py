import os
import stat
import sys

from enum import Enum

class FileGuess:
    def __init__(self, file_type=None, is_special=False):
        self.is_special = is_special
        self.file_type = file_type
        
    def __repr__(self):
        return str(self.file_type) + ": special: " + str(self.is_special)

class FileType:
    class Class:
        MimeType = "$mime"
        VersionControl = "$version"
        BuildSystem = "$build"
        ContinuousIntegration = "$ci"
    
    def __init__(self, clazz, value):
        self.clazz = clazz
        self.value = value
    
    def __repr__(self):
        return self.clazz + " (=" + self.value + ")"

class filetypes:
    
    # MIME types
    mime_directory = FileType(FileType.Class.MimeType, "inode/directory")
    mime_gitignore = FileType(FileType.Class.MimeType, "custom$git/ignore")
    mime_gitattributes = FileType(FileType.Class.MimeType, "custom$git/attributes")
    mime_python = FileType(FileType.Class.MimeType, "application/x-python")
    mime_symlink = FileType(FileType.Class.MimeType, "inode/symlink")
    mime_text_plain = FileType(FileType.Class.MimeType, "text/plain")
    
    # Version controls
    version_git = FileType(FileType.Class.VersionControl, "git")
                  
    # Build systems
    build_python =  FileType(FileType.Class.BuildSystem, "python")

class Guesser_Inode:
    def guess(self, file):
        if file.is_directory():
            return [FileGuess(filetypes.mime_directory)]
        elif os.path.islink(file.path):
            return [FileGuess(filetypes.mime_symlink)]

class Guesser_Git:
    def guess(self, file):
        if file.basename == ".git":
            return [FileGuess(filetypes.version_git, True)]
        elif file.basename == ".gitignore":
            return [FileGuess(filetypes.mime_gitignore)]
        elif file.basename == ".gitattributes":
            return [FileGuess(filetypes.mime_gitattributes)]

class Guesser_Python:
    def guess(self, file):
        if file.basename == "__pycache__":
            return [FileGuess(filetypes.build_python, True)]
        elif file.extension == ".py":
            return [FileGuess(filetypes.mime_python)]

class Guesser_Generic:
    def guess(self, file):
        if file.extension == ".txt":
            return [FileGuess(filetypes.mime_text_plain)]

def register_all_guessers(registry):
    registry.register_file_type_guesser(Guesser_Generic())
    registry.register_file_type_guesser(Guesser_Git())
    registry.register_file_type_guesser(Guesser_Inode())
    registry.register_file_type_guesser(Guesser_Python())
