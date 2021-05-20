import os
import re
import stat
import sys
import traceback

import config as config

from enum import Enum

from .logging import *

class FileGuess:
    def __init__(self, file_type=None, **attributes):
        self.file_type = file_type
        self.attributes = attributes
        
    def __repr__(self):
        return sgr("1", "FileGuess") + " { " + sgr("3;34", "type: ") + str(self.file_type) + "; " + sgr("3;34", "attributes: ") + str(self.attributes) + " }"
    
    def to_user_readable_string(self):
        output = ""
        output += self.file_type.to_user_readable_string() + "\n"
        
        for name, value in self.attributes.items():
            output += "   - " + name + ": " + str(value) + "\n"
        
        return output

    def collapse_attribute(self, name, value):
        if not name in self.attributes:
            self.attributes[name] = value
            return

        if isinstance(self.attributes[name], bool):
            self.attributes[name] |= value
        elif isinstance(self.attributes[name], int):
            self.attributes[name] += value

    def is_special(self):
        return self.attributes.get("special")
    
    def is_source(self):
        return self.attributes.get("source")
    
    def lines_of_code(self):
        return self.attributes.get("lines_of_code")
    
    def file_count(self):
        return self.attributes.get("file_count")

def guess_source_file(filetype, file):
    
    if config.args.no_open:
        lines_of_code = 0
    else:
        fd = file.descriptor()
        if fd != None:
            try:
                with fd as _file:
                    lines_of_code = sum(1 for _ in _file)
            except:
                print_error(sys.exc_info())
                lines_of_code = 0
        else:
            lines_of_code = 0

    return FileGuess(filetype, source=True, lines_of_code=lines_of_code, file_count=1)

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
    
    def to_user_readable_string(self):
        output = ""
        
        # FIXME: Make it better!
        if self.clazz == FileType.Class.MimeType:
            output += "MIME Type"
        elif self.clazz == FileType.Class.VersionControl:
            output += "Version control"
        elif self.clazz == FileType.Class.BuildSystem:
            output += "Build system"
        elif self.clazz == FileType.Class.ContinuousIntegration:
            output += "Continuous Integration"
        
        output = sgr("1;32", output)
        
        output += ": "
        output += sgr("3;35", self.value)
        return output

class filetypes:
    
    # MIME types
    mime_cpp = FileType(FileType.Class.MimeType, "text/x-c")
    mime_directory = FileType(FileType.Class.MimeType, "inode/directory")
    mime_gitignore = FileType(FileType.Class.MimeType, "custom$git/ignore")
    mime_gitattributes = FileType(FileType.Class.MimeType, "custom$git/attributes")
    mime_java = FileType(FileType.Class.MimeType, "text/x-java-source")
    mime_js = FileType(FileType.Class.MimeType, "application/js")
    mime_python = FileType(FileType.Class.MimeType, "application/x-python")
    mime_symlink = FileType(FileType.Class.MimeType, "inode/symlink")
    mime_text_plain = FileType(FileType.Class.MimeType, "text/plain")
    
    # Version controls
    version_git = FileType(FileType.Class.VersionControl, "git")
                  
    # Build systems
    build_cmake =  FileType(FileType.Class.BuildSystem, "cmake")
    build_gnu_make = FileType(FileType.Class.BuildSystem, "gnu_make")
    build_gradle = FileType(FileType.Class.BuildSystem, "gradle")
    build_gulp = FileType(FileType.Class.BuildSystem, "gulp")
    build_node_js = FileType(FileType.Class.BuildSystem, "node_js")
    build_python =  FileType(FileType.Class.BuildSystem, "python")

class Guesser:
    def guess(self, file):
        return []

class Guesser_Cpp(Guesser):
    def guess(self, file):
        if file.basename == "CMakeLists.txt":
            return [FileGuess(filetypes.build_cmake)]
        elif file.basename == "Makefile":
            return [FileGuess(filetypes.build_gnu_make)]
        elif file.extension == ".c" or file.extension == ".cpp" or file.extension == ".h" or file.extension == ".hpp" or \
             file.extension == ".cxx" or file.extension == ".cc" or file.extension == ".hxx":
            return [guess_source_file(filetypes.mime_cpp, file)]

class Guesser_Generic(Guesser):
    def guess(self, file):
        if file.extension == ".txt":
            return [FileGuess(filetypes.mime_text_plain)]

class Guesser_Git(Guesser):
    def guess(self, file):
        if file.basename == ".git":
            return [FileGuess(filetypes.version_git, special=True)]
        elif file.basename == ".gitignore":
            return [FileGuess(filetypes.mime_gitignore)]
        elif file.basename == ".gitattributes":
            return [FileGuess(filetypes.mime_gitattributes)]

class Guesser_Inode(Guesser):
    def guess(self, file):
        if file.is_directory():
            return [FileGuess(filetypes.mime_directory, subfile_count=len(file.files.keys()))]
        elif os.path.islink(file.path):
            return [FileGuess(filetypes.mime_symlink, target=os.readlink(file.path))]
        
class Guesser_Java(Guesser):
    def guess(self, file):
        if file.basename == "gradlew" or file.basename == "gradlew.bat" or file.basename == "gradle.properties" or file.basename == "build.gradle":
            return [FileGuess(filetypes.build_gradle)]
        elif file.extension == ".java":
            return [guess_source_file(filetypes.mime_java, file)]

class Guesser_JavaScript(Guesser):
    def guess(self, file):
        if file.basename == "package.json" or file.basename == "package-lock.json":
            return [FileGuess(filetypes.build_node_js)]
        elif file.basename == "node_modules":
            return [FileGuess(filetypes.build_node_js, special=True)]
        elif re.search("^gulpfile\..*\.js$", file.basename):
            return [FileGuess(filetypes.build_gulp)]
        elif file.extension == ".js":
            return [guess_source_file(filetypes.mime_js, file)]

class Guesser_Python(Guesser):
    def guess(self, file):
        if file.basename == "__pycache__":
            return [FileGuess(filetypes.build_python, special=True)]
        elif file.extension == ".py":
            return [guess_source_file(filetypes.mime_python, file)]

def register_all_guessers(registry):
    registry.register_file_type_guesser("cpp",     Guesser_Cpp())
    registry.register_file_type_guesser("generic", Guesser_Generic())
    registry.register_file_type_guesser("git",     Guesser_Git())
    registry.register_file_type_guesser("inode",   Guesser_Inode())
    registry.register_file_type_guesser("java",    Guesser_Java())
    registry.register_file_type_guesser("js",      Guesser_JavaScript())
    registry.register_file_type_guesser("python",  Guesser_Python())
