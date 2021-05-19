import os
import stat
import sys

from enum import Enum

from .logging import *

class FileGuess:
    def __init__(self, file_type=None, **attributes):
        self.file_type = file_type
        self.attributes = attributes
        
    def __repr__(self):
        return sgr("1", "FileGuess") + " { " + sgr("3;34", "type: ") + str(self.file_type) + "; " + sgr("3;34", "attributes: ") + str(self.attributes) + " }"

    def is_special(self):
        return self.attributes.get("special")
    
    def is_source(self):
        return self.attributes.get("source")
    
    def lines_of_code(self):
        return self.attributes.get("lines_of_code")

def guess_source_file(filetype, file):
    
    with file.descriptor() as file:
        lines_of_code = sum(1 for _ in file)

    return FileGuess(filetype, source=True, lines_of_code=lines_of_code)

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
        return sgr("1;33", self.clazz) + " (" + sgr("3;32", self.value) + ")"

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

class Guesser:
    def guess(self, file):
        return []

class Guesser_Inode(Guesser):
    def guess(self, file):
        if file.is_directory():
            return [FileGuess(filetypes.mime_directory)]
        elif os.path.islink(file.path):
            return [FileGuess(filetypes.mime_symlink)]

class Guesser_Git(Guesser):
    def guess(self, file):
        if file.basename == ".git":
            return [FileGuess(filetypes.version_git, special=True)]
        elif file.basename == ".gitignore":
            return [FileGuess(filetypes.mime_gitignore)]
        elif file.basename == ".gitattributes":
            return [FileGuess(filetypes.mime_gitattributes)]

class Guesser_Python(Guesser):
    def guess(self, file):
        if file.basename == "__pycache__":
            return [FileGuess(filetypes.build_python, special=True)]
        elif file.extension == ".py":
            return [guess_source_file(filetypes.mime_python, file)]

class Guesser_Generic(Guesser):
    def guess(self, file):
        if file.extension == ".txt":
            return [FileGuess(filetypes.mime_text_plain)]

def register_all_guessers(registry):
    registry.register_file_type_guesser(Guesser_Generic())
    registry.register_file_type_guesser(Guesser_Git())
    registry.register_file_type_guesser(Guesser_Inode())
    registry.register_file_type_guesser(Guesser_Python())
