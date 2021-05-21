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
        self.guesser = "unknown"
        
    def __repr__(self):
        return sgr("1", "FileGuess") + " { " + sgr("3;34", "type: ") + str(self.file_type) + "; " + sgr("3;34", "attributes: ") + str(self.attributes) + " }"
    
    def to_user_readable_string(self):
        output = ""
        output += self.file_type.to_user_readable_string() + sgr("32", " (" + self.guesser + ")\n")
        
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
            except KeyboardInterrupt:
                raise
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
    
    def __init__(self, clazz, value, user_readable_value=None):
        self.clazz = clazz
        self.value = value
        self.user_readable_value = user_readable_value if user_readable_value != None else value
    
    def __repr__(self):
        return sgr("1;33", self.clazz) + " (" + sgr("3;32", self.value) + ")"
    
    def to_user_readable_string(self):
        output = ""
        
        # FIXME: Make it better!
        if self.clazz == FileType.Class.MimeType:
            output += "Format/Language"
        elif self.clazz == FileType.Class.VersionControl:
            output += "Version control"
        elif self.clazz == FileType.Class.BuildSystem:
            output += "Build system"
        elif self.clazz == FileType.Class.ContinuousIntegration:
            output += "Continuous Integration"
        
        output = sgr("1;32", output)
        
        output += ": "
        output += self.to_fancy_string()
        return output
    
    def to_fancy_string(self):
        return sgr("3;35", self.user_readable_value) + sgr("3;36", " (" + self.value + ")")

class filetypes:
    
    # MIME types
    mime_cmake = FileType(FileType.Class.MimeType,          "custom$cmake", "CMake")
    mime_cpp = FileType(FileType.Class.MimeType,            "text/x-c", "C/C++")
    mime_css = FileType(FileType.Class.MimeType,            "text/css", "CSS")
    mime_directory = FileType(FileType.Class.MimeType,      "inode/directory", "Directory")
    mime_gitignore = FileType(FileType.Class.MimeType,      "custom$git/ignore", ".gitignore file")
    mime_gitattributes = FileType(FileType.Class.MimeType,  "custom$git/attributes", ".gitattributes file")
    mime_html = FileType(FileType.Class.MimeType,           "text/html", "HTML")
    mime_java = FileType(FileType.Class.MimeType,           "text/x-java-source", "Java")
    mime_jpg = FileType(FileType.Class.MimeType,            "image/jpg", "JPG image")
    mime_js = FileType(FileType.Class.MimeType,             "application/js", "JavaScript")
    mime_makefile = FileType(FileType.Class.MimeType,       "custom$makefile", "Makefile")
    mime_markdown = FileType(FileType.Class.MimeType,       "custom$markdown", "Markdown")
    mime_php = FileType(FileType.Class.MimeType,            "custom$php", "PHP")
    mime_png = FileType(FileType.Class.MimeType,            "image/png", "PNG image")
    mime_python = FileType(FileType.Class.MimeType,         "application/x-python", "Python")
    mime_symlink = FileType(FileType.Class.MimeType,        "inode/symlink", "Symlink")
    mime_text_plain = FileType(FileType.Class.MimeType,     "text/plain", "Plain text")
    
    @staticmethod
    def mime_unknown(ext):
        return FileType(FileType.Class.MimeType, "?(" + ext + ")", "Unknown (" + ext + ")")
    
    # Version controls
    version_git = FileType(FileType.Class.VersionControl,   "git", "Git")
                  
    # Build systems
    build_cmake =  FileType(FileType.Class.BuildSystem,     "cmake", "CMake")
    build_gnu_make = FileType(FileType.Class.BuildSystem,   "gnu_make", "GNU Make")
    build_gradle = FileType(FileType.Class.BuildSystem,     "gradle", "Gradle")
    build_gulp = FileType(FileType.Class.BuildSystem,       "gulp", "Gulp")
    build_node_js = FileType(FileType.Class.BuildSystem,    "node_js", "Node.js")
    build_python =  FileType(FileType.Class.BuildSystem,    "python", "Python (__pycache__)")
    
    # CI
    ci_github_actions = FileType(FileType.Class.ContinuousIntegration, "github_actions", "GitHub Actions")
    ci_travis = FileType(FileType.Class.ContinuousIntegration,         "travis", "Travis")

class Guesser:
    def __init__(self):
        self.name = "unknown"
    
    def guess(self, file):
        return []
    
class Guesser_CI:
    def guess(self, file):
        if file.basename == "travis.yml":
            return [FileGuess(filetypes.ci_travis)]
        if file.parent != None and file.parent.basename == ".github" and file.basename == "workflows":
            return [FileGuess(filetypes.ci_github_actions, special=True)]

class Guesser_Cpp(Guesser):
    def guess(self, file):
        if file.basename == "CMakeLists.txt" or file.extension == ".cmake":
            return [FileGuess(filetypes.build_cmake, file_count=1), guess_source_file(filetypes.mime_cmake, file)]
        elif file.basename == "CMakeFiles":
            return [FileGuess(filetypes.build_cmake, special=True)]
        elif file.basename == "Makefile":
            return [FileGuess(filetypes.build_gnu_make, file_count=1), guess_source_file(filetypes.mime_makefile, file)]
        elif file.extension == ".c" or file.extension == ".cpp" or file.extension == ".h" or file.extension == ".hpp" or \
             file.extension == ".cxx" or file.extension == ".cc" or file.extension == ".hxx":
            return [guess_source_file(filetypes.mime_cpp, file)]

class Guesser_Generic(Guesser):
    def guess(self, file):
        if file.extension == ".txt":
            return [guess_source_file(filetypes.mime_text_plain, file)]
        else:
            return [FileGuess(filetypes.mime_unknown(file.extension), file_count=1, lines_of_code=1, unknown=True)]

class Guesser_Git(Guesser):
    def guess(self, file):
        if file.basename == ".git":
            return [FileGuess(filetypes.version_git, special=True)]
        elif file.basename == ".gitignore":
            return [FileGuess(filetypes.mime_gitignore, file_count=1)]
        elif file.basename == ".gitattributes":
            return [FileGuess(filetypes.mime_gitattributes, file_count=1)]

class Guesser_Image(Guesser):
    def guess(self, file):
        if file.extension == ".jpg":
            return [FileGuess(filetypes.mime_jpg)]
        elif file.extension == ".png":
            return [FileGuess(filetypes.mime_png)]

class Guesser_Inode(Guesser):
    def guess(self, file):
        if file.is_directory():
            return [FileGuess(filetypes.mime_directory, subfile_count=len(file.files.keys()))]
        elif os.path.islink(file.path):
            return [FileGuess(filetypes.mime_symlink, target=os.readlink(file.path))]
        
class Guesser_Java(Guesser):
    def guess(self, file):
        if file.basename == "gradlew" or file.basename == "gradlew.bat" or file.basename == "gradle.properties" or file.basename == "build.gradle":
            return [FileGuess(filetypes.build_gradle, file_count=1)]
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

class Guesser_Markup(Guesser):
    def guess(self, file):
        if file.extension == ".html" or file.extension == ".htm":
            return [guess_source_file(filetypes.mime_html, file)]
        elif file.extension == ".md":
            return [guess_source_file(filetypes.mime_markdown, file)]

class Guesser_Python(Guesser):
    def guess(self, file):
        if file.basename == "__pycache__":
            return [FileGuess(filetypes.build_python, file_count=1, special=True)]
        elif file.extension == ".py":
            return [guess_source_file(filetypes.mime_python, file)]

class Guesser_Web(Guesser):
    def guess(self, file):
        if file.extension == ".php":
            return [guess_source_file(filetypes.mime_php, file)]
        elif file.extension == ".css":
            return [guess_source_file(filetypes.mime_css, file)]
        

def register_all_guessers(registry):
    registry.register_file_type_guesser("ci",      Guesser_CI())
    registry.register_file_type_guesser("cpp",     Guesser_Cpp())
    registry.register_file_type_guesser("git",     Guesser_Git())
    registry.register_file_type_guesser("image",   Guesser_Image())
    registry.register_file_type_guesser("inode",   Guesser_Inode())
    registry.register_file_type_guesser("java",    Guesser_Java())
    registry.register_file_type_guesser("js",      Guesser_JavaScript())
    registry.register_file_type_guesser("markup",  Guesser_Markup())
    registry.register_file_type_guesser("python",  Guesser_Python())
    registry.register_file_type_guesser("web",     Guesser_Web())
    
    # Low priority
    registry.register_file_type_guesser("generic", Guesser_Generic(), priority=100)
