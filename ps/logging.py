import os
import sys

import config as config

class __internal__:
    ansi_enabled = None

def allow_ansi_escape_codes():
    if __internal__.ansi_enabled == None:
        supported = os.name == "posix"
        enabled = os.isatty(1) and not config.args.disable_formatting
        __internal__.ansi_enabled = supported and enabled
    return __internal__.ansi_enabled
    

def sgr(code, text):
    return ("\033[" + str(code) + "m" + str(text) + "\033[0m") if allow_ansi_escape_codes() else text

def print_error(text):
    print(sgr("1;31", "[ERROR]"), sgr("31", text), file=sys.stderr)

def print_verbose(text):
    if config.args.verbose:
        print(sgr("1;35", "[VERBOSE]"), sgr("35", text), file=sys.stderr)
    print_status("verbose", text)

def print_status(status, text):
    if not allow_ansi_escape_codes():
        # we can't do anything with these terminals :(
        print(text)
        return
    
    text = text[0:100]
    if len(text) != 0:
        print("\033[G\033[2K\033[21;23;92m{}\033[m".format(text), end="") # goto column 1, print status, clear line
    else:
        print("\033[G\033[2K", end="") # just clear line
