import os
import platform
import sys

import config as config

class __internal__:
    ansi_enabled = None
    unicode_enabled = None

def allow_ansi_escape_codes():
    if __internal__.ansi_enabled == None:
        supported = os.name == "posix" and os.isatty(1)
        __internal__.ansi_enabled = supported and not config.args.no_formatting
    return __internal__.ansi_enabled
    

def allow_unicode():
    if __internal__.unicode_enabled == None:
        supported = sys.stdout.encoding.lower().startswith('utf')
        __internal__.unicode_enabled = supported and not config.args.no_unicode
    return __internal__.unicode_enabled
    

def sgr(code, text):
    return ("\033[" + str(code) + "m" + str(text) + "\033[0m") if allow_ansi_escape_codes() else text

def unicode(text):
    def replace_unicode_characters(text):
        text = text.replace("•", "*")
        text = text.replace("╭─", ",-")
        text = text.replace("─", "-")
        text = text.replace("│", "|")
        text = text.replace("▀", "#")
        text = text.replace("→", "->")
        return text
    
    return text if allow_unicode() else replace_unicode_characters(text)

def print_error(text):
    print(sgr("1;31", "[ERROR]"), sgr("31", text), file=sys.stderr)

def print_verbose(text):
    if config.args.verbose:
        print(sgr("1;35", "[VERBOSE]"), sgr("35", text), file=sys.stderr)
    print_status("verbose", text)

def print_status(status, text = ""):
    if not allow_ansi_escape_codes():
        # we can't do anything with these terminals :(
        return
    
    text = text[0:100]
    if len(text) != 0:
        print("\033[G\033[2K\033[21;23;92m{}\033[m".format(text), end="") # goto column 1, print status, clear line
    else:
        print("\033[G\033[2K", end="") # just clear line
