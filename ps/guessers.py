import os
import re
import stat
import sys
import traceback

from enum import Enum
from io import StringIO

import config as config
from .logging import *
from .util import *

class FileGuess:
    def __init__(self, file_type=None, **attributes):
        self.file_type = file_type
        self.attributes = attributes
        self.guesser = "unknown"
        
    def __repr__(self):
        return sgr("1", "FileGuess") + " { " + sgr("3;34", "type: ") + str(self.file_type) + "; " + sgr("3;34", "attributes: ") + str(self.attributes) + " }"
    
    def to_user_readable_string(self):
        output = ""
        output += self.file_type.to_user_readable_string() + sgr("32", " (" + self.guesser.name + ")\n")
        
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

    return FileGuess(filetype, source=True, lines_of_code=lines_of_code)

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
    
    @staticmethod
    def mime(value, description):
        return FileType(FileType.Class.MimeType, value, description)
    
    @staticmethod
    def version_control(value, description):
        return FileType(FileType.Class.VersionControl, value, description)
    
    @staticmethod
    def build_system(value, description):
        return FileType(FileType.Class.BuildSystem, value, description)
    
    @staticmethod
    def continuous_integration(value, description):
        return FileType(FileType.Class.ContinuousIntegration, value, description)
    
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
    mime_asm =              FileType.mime("text/x-asm", "Assembly")
    mime_bmp =              FileType.mime("image/bmp", "BMP image")
    mime_cmake =            FileType.mime("custom$cmake", "CMake")
    mime_config =           FileType.mime("custom$config", "Config")
    mime_cpp =              FileType.mime("text/x-c", "C/C++")
    mime_css =              FileType.mime("text/css", "CSS")
    mime_directory =        FileType.mime("inode/directory", "Directory")
    mime_doc =              FileType.mime("application/msword", "MS Word document")
    mime_docker =           FileType.mime("custom$docker", "Dockerfile")
    mime_dynamic_library =  FileType.mime("custom$dynamic_library", "Dynamic library")
    mime_elf =              FileType.mime("custom$elf", "ELF binary")
    mime_gif =              FileType.mime("image/gif", "GIF image")
    mime_gitignore =        FileType.mime("custom$git/ignore", ".gitignore")
    mime_gitattributes =    FileType.mime("custom$git/attributes", ".gitattributes")
    mime_gz =               FileType.mime("application/x-compressed$gz", "Gzip-compressed file")
    mime_html =             FileType.mime("text/html", "HTML")
    mime_ico =              FileType.mime("image/x-icon", "Icon (ICO)")
    mime_ini =              FileType.mime("custom$ini", "INI config")
    mime_jar =              FileType.mime("custom$jar", "JAR")
    mime_java =             FileType.mime("text/x-java-source", "Java")
    mime_jpg =              FileType.mime("image/jpg", "JPG image")
    mime_js =               FileType.mime("application/js", "JavaScript")
    mime_json =             FileType.mime("application/json", "JSON")
    mime_ld_script =        FileType.mime("custom$ld", "Linker script")
    mime_makefile =         FileType.mime("custom$makefile", "Makefile")
    mime_markdown =         FileType.mime("custom$markdown", "Markdown")
    mime_mp3 =              FileType.mime("sound/mp3", "MP3 sound")
    mime_ninja =            FileType.mime("custom$ninja", "Ninja config")
    mime_object =           FileType.mime("custom$object", "Object")
    mime_ods =              FileType.mime("custom$ods", "OpenOffice Spreadsheet document")
    mime_odt =              FileType.mime("custom$odt", "OpenOffice Writer document")
    mime_ogg =              FileType.mime("sound/ogg", "OGG sound")
    mime_patch =            FileType.mime("custom$patch", "Patch/diff")
    mime_pe =               FileType.mime("custom$pe", "Portable Executable image")
    mime_pdf =              FileType.mime("application/pdf", "PDF document")
    mime_php =              FileType.mime("custom$php", "PHP")
    mime_png =              FileType.mime("image/png", "PNG image")
    mime_python =           FileType.mime("application/x-python", "Python")
    mime_shell =            FileType.mime("application/x-sh", "Shell")
    mime_static_library =   FileType.mime("custom$static_library", "Static library")
    mime_svg =              FileType.mime("custom$svg", "SVG image")
    mime_symlink =          FileType.mime("inode/symlink", "Symlink")
    mime_tar =              FileType.mime("application/x-tar", "Tar archive")
    mime_text_plain =       FileType.mime("text/plain", "Plain text")
    mime_ttf =              FileType.mime("font/ttf", "TTF font")
    mime_wasm =             FileType.mime("custom$wasm", "WebAssembly")
    mime_wav =              FileType.mime("sound/wav", "WAV sound")
    mime_xls =              FileType.mime("application/excel", "MS Excel document")
    mime_yaml =             FileType.mime("custom$yaml", "YML")
    mime_zip =              FileType.mime("application/x-zip-compressed", "ZIP archive")
    
    @staticmethod
    def mime_unknown(ext):
        return FileType.mime("?(" + ext + ")", "Unknown (" + ext + ")")
    
    # Version controls
    version_git = FileType.version_control("git", "Git")
                  
    # Build systems
    build_cmake =  FileType.build_system("cmake", "CMake")
    build_docker =  FileType.build_system("docker", "Docker")
    build_gnu_make = FileType.build_system("gnu_make", "GNU Make")
    build_gradle = FileType.build_system("gradle", "Gradle")
    build_gulp = FileType.build_system("gulp", "Gulp")
    build_ninja = FileType.build_system("ninja", "Ninja")
    build_node_js = FileType.build_system("node_js", "Node.js")
    build_python =  FileType.build_system("python", "Python (__pycache__)")
    
    # CI
    ci_github_actions = FileType.continuous_integration("github_actions", "GitHub Actions")
    ci_travis = FileType.continuous_integration("travis", "Travis")

class Guesser:
    def __init__(self, description=None):
        self.name = "unknown"
        self.description = description
    
    def guess(self, file):
        return []
    
    def print_additional_info(self):
        if self.description != None:
            print(" - " + sgr("3;38;2;208;208;208", self.description), end="")

class MagicGuesser(Guesser):
    def __init__(self, description):
        Guesser.__init__(self, description)
        self.subguessers = []
        
    def register_subguesser(self, magic, filetype, **attributes):
        self.subguessers.append((magic, filetype, attributes))
        
    def guess(self, file):
        fd = file.descriptor()
        if fd == None:
            return []
        for magic, filetype, attributes in self.subguessers:
            fd.seek(0)
            bytes = fd.read(len(magic))
            if bytes == magic:
                return [FileGuess(filetype, *attributes)]
        return []
    
    def print_additional_info(self):
        Guesser.print_additional_info(self)
        
        for subguesser in self.subguessers:
            print()
            print("   - " + str(subguesser[0]) + " → " + str(subguesser[1]), end="")

class BuildSystemGuesser(Guesser):
    
    # All commands return None if operation is not supported, True on success,
    # False on error. Output format is not standarized across build systems.
    def run(self, file, args):
        pass
    
    def configure(self, file, args):
        pass
    
    def build(self, file, args):
        pass
    
    def clean(self, file, args):
        pass
    
    # `type` can be one of `targets`, `dependencies`
    def info(self, file, type, args):
        pass

class Guesser_CMake(BuildSystemGuesser):
    def guess(self, file):
        if file.basename == "CMakeLists.txt" or file.extension == ".cmake":
            return [FileGuess(filetypes.build_cmake), guess_source_file(filetypes.mime_cmake, file)]
        elif file.basename == "CMakeFiles":
            return [FileGuess(filetypes.build_cmake, special=True)]
        
    # TODO: Call the underlying (generated) build system for
    # some commands!
    def run(self, file, args):
        return None #TODO
    
    def configure(self, file, args):
        directory = args.get("directory")
        directory = directory if directory != None else "build"
        args = args.get("args")
        args = args if args != None else ""
        return run_process_in_dir(file.path, "cmake -B {} {}".format(directory, args))
    
    def build(self, file, args):
        target = args.get("target")
        if target == None:
            target = ""
        else:
            target = "--target {}".format(target)
        directory = args.get("directory")
        directory = directory if directory != None else "build"
        args = args.get("args")
        args = args if args != None else ""
        # TODO: Use multiple jobs
        return run_process_in_dir(file.path, "cmake --build {} {} {}".format(directory, target, args))

    def clean(self, file, args):
        # It should be called by generated build system
        return None
    
    def info(self, file, type, args):
        # This is TODO.
        # I've seen something like BUILDSYSTEM_TARGETS but
        # I still don't know how to use it here...
        return None

class Guesser_GNUMake(BuildSystemGuesser):
    def guess(self, file):
        if re.search("Makefile.*", file.basename):
            return [FileGuess(filetypes.build_gnu_make), guess_source_file(filetypes.mime_makefile, file)]
        
    def run(self, file, args):
        return None #TODO
    
    def configure(self, file, args):
        # Not applicable
        return None

    def build(self, file, args):
        target = args.get("target")
        if target == None:
            print_error("You must specify a target!")
        args = args.get("args")
        args = args if args != None else ""
        # TODO: Use multiple jobs
        return run_process_in_dir(file.path, "make {} {}".format(target, args))

    def clean(self, file, args):
        return run_process_in_dir(file.path, "make clean")
    
    def info(self, file, type, args):
        if type == "targets":
            return run_process_in_dir(file.path, "make help")
        return None

class Guesser_Ninja(BuildSystemGuesser):
    def guess(self, file):
        if file.extension == ".ninja":
            return [FileGuess(filetypes.build_ninja), guess_source_file(filetypes.mime_ninja, file)]
        
    def run(self, file, args):
        return None #TODO
    
    def configure(self, file, args):
        # Not applicable
        return None

    def build(self, file, args):
        target = args.get("target")
        if target == None:
            print_error("You must specify a target!")
        args = args.get("args")
        args = args if args != None else ""
        # TODO: Use multiple jobs
        return run_process_in_dir(file.path, "ninja {} {}".format(target, args))

    def clean(self, file, args):
        return run_process_in_dir(file.path, "ninja clean")
    
    def info(self, file, type, args):
        if type == "targets":
            return run_process_in_dir(file.path, "ninja help")
        return None
    
class Guesser_Node(BuildSystemGuesser):
    def guess(self, file):
        if file.basename == "package.json" or file.basename == "package-lock.json":
            return [FileGuess(filetypes.build_node_js)]
        
    def run(self, file, args):
        return None #TODO
    
    def configure(self, file, args):
        return run_process_in_dir(file.path, "npm install")

    def build(self, file, args):
        # Not applicable.
        return None

    def clean(self, file, args):
        # TODO: Maybe we can remove `node_modules`?
        return None
    
    def info(self, file, type, args):
        if type == "dependencies":
            return run_process_in_dir(file.path, "npm list")

        return None

class Guesser_Pycache(Guesser):
    def guess(self, file):
        if file.basename == "__pycache__":
            return [FileGuess(filetypes.build_python, special=True)]
        
    def run(self, file, args):
        return None #TODO
    
    def configure(self, file, args):
        return None #TODO

    def build(self, file, args):
        return None #TODO

    def clean(self, file, args):
        return None #TODO
    
    def info(self, file, type, args):
        return None #TODO
    

# Source guessers!
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
            return [FileGuess(filetypes.mime_gz)]
        elif file.extension == ".tar":
            return [FileGuess(filetypes.mime_tar)]
        elif file.extension == ".zip":
            return [FileGuess(filetypes.mime_zip)]

class Guesser_Cpp(Guesser):
    def guess(self, file):
        if file.extension == ".c" or file.extension == ".cpp" or file.extension == ".h" or file.extension == ".hpp" or \
             file.extension == ".cxx" or file.extension == ".cc" or file.extension == ".hxx":
            return [guess_source_file(filetypes.mime_cpp, file)]
        elif file.extension == ".o":
            return [FileGuess(filetypes.mime_object)]
        elif file.extension == ".ld":
            return [guess_source_file(filetypes.mime_ld_script, file)]
        elif file.extension == ".a":
            return [FileGuess(filetypes.mime_static_library)]
        elif file.extension == ".dll":
            return [FileGuess(filetypes.mime_dynamic_library)]

class Guesser_Docker(Guesser):
    def guess(self, file):
        if file.basename == "Dockerfile" or file.extension == ".dockerfile":
            return [guess_source_file(filetypes.mime_docker, file)]

class Guesser_Document(Guesser):
    def guess(self, file):
        if file.extension == ".doc" or file.extension == ".docx":
            return [FileGuess(filetypes.mime_doc)]
        elif file.extension == ".xls" or file.extension == ".xlsx":
            return [FileGuess(filetypes.mime_xls)]

        elif file.extension == ".odt":
            return [FileGuess(filetypes.mime_odt)]
        elif file.extension == ".ods":
            return [FileGuess(filetypes.mime_ods)]
        
        elif file.extension == ".pdf":
            return [FileGuess(filetypes.mime_pdf)]

class Guesser_Font(Guesser):
    def guess(self, file):
        if file.extension == ".ttf":
            return [FileGuess(filetypes.mime_ttf)]

class Guesser_Generic(Guesser):
    def guess(self, file):
        if file.extension == ".txt":
            return [guess_source_file(filetypes.mime_text_plain, file)]
        else:
            return [FileGuess(filetypes.mime_unknown(file.extension), unknown=True)]

class VersionControlGuesser(Guesser):
    def print_log(self, file, format):
        print_error("Invalid VersionControlGuesser")
        return None
    
    def fancy_display_commit(self, data, format="default"):
        author = data["author"]
        if format == "compact":
            return "{} ({}): {}".format(sgr("1;33", author["full_name"]), sgr("35", data["date"]), sgr("3", data["message"][4:]))
        elif format == "no-version":
            return "{}, {}: \n{}\n{}".format(sgr("1;33", author["full_name"]), sgr("35", data["date"]), data["message"], sgr("90;3", data["description"]))
        else:
            return "{} by {} {} at {}\n\n{}\n{}".format(sgr("4;34", data["hash"]), sgr("1;33", author["full_name"]), sgr("33", "<" + author["email"] + ">"),
                                                        sgr("35", data["date"]), data["message"], sgr("90;3", data["description"]))

class Guesser_Git(VersionControlGuesser):
    def parse_git_log_output(self, output):
        data = []
        
        while True:
            # If the first match fails, probably we reached EOF :)
            try:
                hash = re.search("commit ([a-f0-9]{40})", output.readline().decode()).group(1)
                
                author_regex = re.search("Author: (.*) <(.*)>", output.readline().decode())
                author = {"full_name": author_regex.group(1), "email": author_regex.group(2)}
                date = re.search("Date:   (.*)", output.readline().decode()).group(1)
                output.readline() # Skip empty line
                message = output.readline().decode()
                description = ""
            except:
                break
            
            output.readline() # Skip empty line
            next_line = output.peek().decode()
            if not next_line.startswith('    '):
                # No description
                pass
            else:
                while True:
                    next_line = output.readline().decode()

                    if not next_line.startswith("    "):
                        break

                    description += next_line
            
            if description == "":
                description = "    <No description>\n"
            data.append({"hash":hash, "author":author, "date":date, "message":message, "description":description})
        output.close()
        return data
    
    def git_guess(self, file):
        guess = FileGuess(filetypes.version_git, special=True)
        
        guess.attributes["commit_count"] = int(run_process_in_dir_and_return_stdout(file.path, "git rev-list --all --count"))
        guess.attributes["refs"] = run_process_in_dir_and_return_stdout(file.path, "git for-each-ref --format=%(refname)").split('\n')
        head = self.parse_git_log_output(run_process_in_dir_and_return_stdout_stream(file.path, "git log HEAD^..HEAD"))
        guess.attributes["head"] = head[0] if len(head) > 0 else {}
            
        return [guess]
    
    def print_log(self, file, format):
        log = self.parse_git_log_output(run_process_in_dir_and_return_stdout_stream(file.path, "git log --reverse"))
        for commit in log:
            print(self.fancy_display_commit(commit, format))
    
    def guess(self, file):
        if file.basename == ".git":
            return self.git_guess(file)
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
            return [FileGuess(filetypes.build_gradle)]
        elif file.extension == ".java":
            return [guess_source_file(filetypes.mime_java, file)]
        elif file.extension == ".jar":
            return [FileGuess(filetypes.mime_jar)]

class Guesser_JavaScript(Guesser):
    def guess(self, file):
        if file.basename == "node_modules":
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
        if file.extension == ".py":
            return [guess_source_file(filetypes.mime_python, file)]

class Guesser_Shell(Guesser):
    def guess(self, file):
        if file.extension == ".sh":
            return [guess_source_file(filetypes.mime_shell, file)]

class Guesser_Sound(Guesser):
    def guess(self, file):
        if file.extension == ".wav":
            return [FileGuess(filetypes.mime_wav)]
        elif file.extension == ".ogg":
            return [FileGuess(filetypes.mime_ogg)]
        elif file.extensino == ".mp3":
            return [FileGuess(filetypes.mime_mp3)]

class Guesser_Web(Guesser):
    def guess(self, file):
        if file.extension == ".php":
            return [guess_source_file(filetypes.mime_php, file)]
        elif file.extension == ".css":
            return [guess_source_file(filetypes.mime_css, file)]
        elif file.extension == ".wasm":
            return [guess_source_file(filetypes.mime_wasm, file)]
        

def register_all_guessers(registry):
    # High priority
    magic_guesser = MagicGuesser("Guesser which uses file patterns to detect formats")
    magic_guesser.register_subguesser(b'\x7fELF', filetypes.mime_elf)
    magic_guesser.register_subguesser(b'PE\0\0',  filetypes.mime_pe)
    registry.register_file_type_guesser("magic",    magic_guesser, priority=-100)
    
    registry.register_file_type_guesser("asm",      Guesser_Assembly("Assembly sources"))
    registry.register_file_type_guesser("ci",       Guesser_CI("Continuous integration files"))
    registry.register_file_type_guesser("cmake",    Guesser_CMake("CMake build system"))
    registry.register_file_type_guesser("compress", Guesser_CompressArchive("Compressed and archive files"))
    registry.register_file_type_guesser("config",   Guesser_ConfigGeneric("Generic config files"))
    registry.register_file_type_guesser("cpp",      Guesser_Cpp("C++ and executable files"))
    registry.register_file_type_guesser("docker",   Guesser_Docker("Docker config files"))
    registry.register_file_type_guesser("document", Guesser_Document("Various document files"))
    registry.register_file_type_guesser("font",     Guesser_Font("Font files"))
    registry.register_file_type_guesser("git",      Guesser_Git("Git config files"))
    registry.register_file_type_guesser("image",    Guesser_Image("Image (picture) files"))
    registry.register_file_type_guesser("inode",    Guesser_Inode("Directories etc."))
    registry.register_file_type_guesser("java",     Guesser_Java("Java sources"))
    registry.register_file_type_guesser("js",       Guesser_JavaScript("JS sources"))
    registry.register_file_type_guesser("make",     Guesser_GNUMake("GNU Make build system"))
    registry.register_file_type_guesser("markup",   Guesser_Markup("Markup/formatting languages"))
    registry.register_file_type_guesser("ninja",    Guesser_Ninja("Ninja build system"))
    registry.register_file_type_guesser("node",     Guesser_Node("Node.js / NPM build system"))
    registry.register_file_type_guesser("pycache",  Guesser_Pycache("Python runtime (__pycache__)"))
    registry.register_file_type_guesser("python",   Guesser_Python("Python sources"))
    registry.register_file_type_guesser("shell",    Guesser_Shell("Shell scripts"))
    registry.register_file_type_guesser("web",      Guesser_Web("Web-related formats"))
    
    # Low priority
    registry.register_file_type_guesser("generic", Guesser_Generic("Plaintext and unknown files"), priority=100)
