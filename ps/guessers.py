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
    mime_asm = FileType(FileType.Class.MimeType,             "text/x-asm", "Assembly")
    mime_bmp = FileType(FileType.Class.MimeType,             "image/bmp", "BMP image")
    mime_cmake = FileType(FileType.Class.MimeType,           "custom$cmake", "CMake")
    mime_config = FileType(FileType.Class.MimeType,          "custom$config", "Config")
    mime_cpp = FileType(FileType.Class.MimeType,             "text/x-c", "C/C++")
    mime_css = FileType(FileType.Class.MimeType,             "text/css", "CSS")
    mime_directory = FileType(FileType.Class.MimeType,       "inode/directory", "Directory")
    mime_docker = FileType(FileType.Class.MimeType,          "custom$docker", "Dockerfile")
    mime_dynamic_library = FileType(FileType.Class.MimeType, "custom$dynamic_library", "Dynamic library")
    mime_gif = FileType(FileType.Class.MimeType,             "image/gif", "GIF image")
    mime_gitignore = FileType(FileType.Class.MimeType,       "custom$git/ignore", ".gitignore")
    mime_gitattributes = FileType(FileType.Class.MimeType,   "custom$git/attributes", ".gitattributes")
    mime_gz = FileType(FileType.Class.MimeType,              "application/x-compressed$gz", "Gzip-compressed file")
    mime_html = FileType(FileType.Class.MimeType,            "text/html", "HTML")
    mime_ico = FileType(FileType.Class.MimeType,             "image/x-icon", "Icon (ICO)")
    mime_ini = FileType(FileType.Class.MimeType,             "custom$ini", "INI config")
    mime_java = FileType(FileType.Class.MimeType,            "text/x-java-source", "Java")
    mime_jpg = FileType(FileType.Class.MimeType,             "image/jpg", "JPG image")
    mime_js = FileType(FileType.Class.MimeType,              "application/js", "JavaScript")
    mime_json = FileType(FileType.Class.MimeType,            "application/json", "JSON")
    mime_makefile = FileType(FileType.Class.MimeType,        "custom$makefile", "Makefile")
    mime_markdown = FileType(FileType.Class.MimeType,        "custom$markdown", "Markdown")
    mime_ninja = FileType(FileType.Class.MimeType,           "custom$ninja", "Ninja config")
    mime_object = FileType(FileType.Class.MimeType,          "custom$object", "Object")
    mime_patch = FileType(FileType.Class.MimeType,           "custom$patch", "Patch/diff")
    mime_php = FileType(FileType.Class.MimeType,             "custom$php", "PHP")
    mime_png = FileType(FileType.Class.MimeType,             "image/png", "PNG image")
    mime_python = FileType(FileType.Class.MimeType,          "application/x-python", "Python")
    mime_shell = FileType(FileType.Class.MimeType,           "application/x-sh", "Shell")
    mime_static_library = FileType(FileType.Class.MimeType,  "custom$static_library", "Static library")
    mime_svg = FileType(FileType.Class.MimeType,             "custom$svg", "SVG image")
    mime_symlink = FileType(FileType.Class.MimeType,         "inode/symlink", "Symlink")
    mime_tar = FileType(FileType.Class.MimeType,             "application/x-tar", "Tar archive")
    mime_text_plain = FileType(FileType.Class.MimeType,      "text/plain", "Plain text")
    mime_yaml = FileType(FileType.Class.MimeType,            "custom$yaml", "YML")
    mime_zip = FileType(FileType.Class.MimeType,             "application/x-zip-compressed", "ZIP archive")
    
    @staticmethod
    def mime_unknown(ext):
        return FileType(FileType.Class.MimeType, "?(" + ext + ")", "Unknown (" + ext + ")")
    
    # Version controls
    version_git = FileType(FileType.Class.VersionControl,   "git", "Git")
                  
    # Build systems
    build_cmake =  FileType(FileType.Class.BuildSystem,     "cmake", "CMake")
    build_docker =  FileType(FileType.Class.BuildSystem,    "docker", "Docker")
    build_gnu_make = FileType(FileType.Class.BuildSystem,   "gnu_make", "GNU Make")
    build_gradle = FileType(FileType.Class.BuildSystem,     "gradle", "Gradle")
    build_gulp = FileType(FileType.Class.BuildSystem,       "gulp", "Gulp")
    build_ninja = FileType(FileType.Class.BuildSystem,      "ninja", "Ninja")
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

class Guesser_Assembly(Guesser):
    def guess(self, file):
        if file.extension == ".S" or file.extension == ".s" or file.extension == ".asm":
            return [guess_source_file(filetypes.mime_asm, file)]
    
class Guesser_CI(Guesser):
    def guess(self, file):
        if file.basename == "travis.yml":
            return [FileGuess(filetypes.ci_travis)]
        if file.parent != None and file.parent.basename == ".github" and file.basename == "workflows":
            return [FileGuess(filetypes.ci_github_actions, special=True)]

class Guesser_ConfigGeneric(Guesser):
    def guess(self, file):
        if file.extension == ".cfg" or file.extension == ".conf" or file.extension == ".config":
            return [guess_source_file(filetypes.mime_config, file)]
        elif file.extension == ".ini":
            return [guess_source_file(filetypes.mime_ini, file)]
        elif file.extension == ".yaml" or file.extension == ".yml":
            return [guess_source_file(filetypes.mime_yaml, file)]
        
class Guesser_CompressArchive(Guesser):
    def guess(self, file):
        if file.extension == ".gz":
            return [FileGuess(filetypes.mime_gz, file_count=1)]
        elif file.extension == ".tar":
            return [FileGuess(filetypes.mime_tar, file_count=1)]
        elif file.extension == ".zip":
            return [FileGuess(filetypes.mime_zip, file_count=1)]

class Guesser_Cpp(Guesser):
    def guess(self, file):
        if file.basename == "CMakeLists.txt" or file.extension == ".cmake":
            return [FileGuess(filetypes.build_cmake, file_count=1), guess_source_file(filetypes.mime_cmake, file)]
        elif file.basename == "CMakeFiles":
            return [FileGuess(filetypes.build_cmake, special=True)]
        elif re.search("Makefile.*", file.basename):
            return [FileGuess(filetypes.build_gnu_make, file_count=1), guess_source_file(filetypes.mime_makefile, file)]
        elif file.extension == ".ninja":
            return [FileGuess(filetypes.build_ninja, file_count=1), guess_source_file(filetypes.mime_ninja, file)]
        elif file.extension == ".c" or file.extension == ".cpp" or file.extension == ".h" or file.extension == ".hpp" or \
             file.extension == ".cxx" or file.extension == ".cc" or file.extension == ".hxx":
            return [guess_source_file(filetypes.mime_cpp, file)]
        elif file.extension == ".o":
            return [FileGuess(filetypes.mime_object, file_count=1)]
        elif file.extension == ".a":
            return [FileGuess(filetypes.mime_static_library, file_count=1)]
        elif file.extension == ".so" or file.extension == ".dll": #FIXME: Move it to magic guesser when it will be done
            return [FileGuess(filetypes.mime_dynamic_library, file_count=1)]

class Guesser_Docker(Guesser):
    def guess(self, file):
        if file.basename == "Dockerfile" or file.extension == ".dockerfile":
            return [guess_source_file(filetypes.mime_docker, file)]

class Guesser_Generic(Guesser):
    def guess(self, file):
        if file.extension == ".txt":
            return [guess_source_file(filetypes.mime_text_plain, file)]
        else:
            return [FileGuess(filetypes.mime_unknown(file.extension), file_count=1, unknown=True)]

class Guesser_Git(Guesser):
    def guess(self, file):
        if file.basename == ".git":
            return [FileGuess(filetypes.version_git, special=True)]
        elif file.basename == ".gitignore":
            return [guess_source_file(filetypes.mime_gitignore, file)]
        elif file.basename == ".gitattributes":
            return [guess_source_file(filetypes.mime_gitattributes, file)]
        elif file.extension == ".patch" or file.extension == ".diff":
            return [guess_source_file(filetypes.mime_patch, file)]

class Guesser_Image(Guesser):
    def guess(self, file):
        if file.extension == ".gif":
            return [FileGuess(filetypes.mime_png)]
        elif file.extension == ".png":
            return [FileGuess(filetypes.mime_png)]
        elif file.extension == ".svg":
            return [FileGuess(filetypes.mime_svg)]
        elif file.extension == ".jpg":
            return [FileGuess(filetypes.mime_jpg)]
        elif file.extension == ".ico":
            return [FileGuess(filetypes.mime_png)]
        elif file.extension == ".bmp":
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
        elif file.extension == ".json":
            return [guess_source_file(filetypes.mime_json, file)]

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

class Guesser_Shell(Guesser):
    def guess(self, file):
        if file.extension == ".sh":
            return [guess_source_file(filetypes.mime_shell, file)]

class Guesser_Web(Guesser):
    def guess(self, file):
        if file.extension == ".php":
            return [guess_source_file(filetypes.mime_php, file)]
        elif file.extension == ".css":
            return [guess_source_file(filetypes.mime_css, file)]
        

def register_all_guessers(registry):
    registry.register_file_type_guesser("asm",     Guesser_Assembly())
    registry.register_file_type_guesser("ci",      Guesser_CI())
    registry.register_file_type_guesser("asm",     Guesser_CompressArchive())
    registry.register_file_type_guesser("config",  Guesser_ConfigGeneric())
    registry.register_file_type_guesser("cpp",     Guesser_Cpp())
    registry.register_file_type_guesser("docker",  Guesser_Docker())
    registry.register_file_type_guesser("git",     Guesser_Git())
    registry.register_file_type_guesser("image",   Guesser_Image())
    registry.register_file_type_guesser("inode",   Guesser_Inode())
    registry.register_file_type_guesser("java",    Guesser_Java())
    registry.register_file_type_guesser("js",      Guesser_JavaScript())
    registry.register_file_type_guesser("markup",  Guesser_Markup())
    registry.register_file_type_guesser("python",  Guesser_Python())
    registry.register_file_type_guesser("shell",   Guesser_Shell())
    registry.register_file_type_guesser("web",     Guesser_Web())
    
    # Low priority
    registry.register_file_type_guesser("generic", Guesser_Generic(), priority=100)
