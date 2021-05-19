import os
import sys

class __internal__:
    ansi_warned = False
    ansi_enabled = None
    user_disable_formatting = False

def allow_ansi_escape_codes():
    __internal__.ansi_enabled
    if __internal__.ansi_enabled == None:
        supported = os.name == "posix"
        enabled = os.isatty(1) and not __internal__.user_disable_formatting
        if not supported and enabled and not __internal__.ansi_warned:
            print("ANSI escape codes are not supported")
            __internal__.ansi_warned = True
        __internal__.ansi_enabled = supported and enabled
    return __internal__.ansi_enabled
    

def sgr(code, text):
    return ("\033[" + str(code) + "m" + str(text) + "\033[0m") if allow_ansi_escape_codes() else text

def print_error(text):
    print(sgr("31", text), file=sys.stderr)
