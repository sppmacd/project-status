import os
import sys

import config as config

class __internal__:
    ansi_warned = False
    ansi_enabled = None

def allow_ansi_escape_codes():
    if __internal__.ansi_enabled == None:
        supported = os.name == "posix"
        enabled = os.isatty(1) and not config.args.disable_formatting
        if not supported and enabled and not __internal__.ansi_warned:
            print("ANSI escape codes are not supported")
            __internal__.ansi_warned = True
        __internal__.ansi_enabled = supported and enabled
    return __internal__.ansi_enabled
    

def sgr(code, text):
    return ("\033[" + str(code) + "m" + str(text) + "\033[0m") if allow_ansi_escape_codes() else text

def print_error(text):
    print(sgr("1;31", "[ERROR]"), sgr("31", text), file=sys.stderr)

def print_verbose(text):
    if config.args.verbose:
        print(sgr("1;35", "[VERBOSE]"), sgr("35", text), file=sys.stderr)
    
