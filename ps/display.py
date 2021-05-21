import config as config
import math

from .logging import *

def directory_fancy_display(dir):
    # FIXME: Multiple accesses to attribute list!!!
    build_systems = []
    cis = []
    formats = []
    
    def compare_guesses(guess):
        return guess.file_type.value
    
    def compare_source_guesses(guess):
        lines_of_code = guess.lines_of_code()
        return lines_of_code if lines_of_code != None else 0
    
    for guess in dir.collapsed_guesses():
        if guess.file_type.clazz == "$build":
            build_systems.append(guess)
        elif guess.file_type.clazz == "$ci":
            cis.append(guess)
        elif guess.file_type.clazz == "$mime":
            formats.append(guess)

    build_systems.sort(key=compare_guesses)
    cis.sort(key=compare_guesses)
    formats.sort(key=compare_source_guesses)
    
    total_lines_of_code = 0
    for guess in formats:
        lines_of_code = guess.lines_of_code()
        total_lines_of_code += (lines_of_code if lines_of_code != None else 0)
    
    if total_lines_of_code == 0:
        return
        
    # TODO: Detect terminal size
    display_size = 150
    total_line_count = 0
    
    for guess in formats:
        lines_of_code = guess.lines_of_code()
        format_display_size = (lines_of_code if lines_of_code != None else 0) * display_size / total_lines_of_code
        guess.attributes["format_display_size"] = format_display_size
    print()
    
    for i in range(len(formats) + 1):
    
        if i < len(formats):
            for j in range(i + 1):
                if int(formats[j].attributes["format_display_size"]) > 0:
                    if j == i:
                        print(sgr("34", "┌─ ") + formats[j].file_type.to_fancy_string() + " - " + sgr("1", str(formats[j].lines_of_code())) + " lines of code")
                    else:
                        print(sgr("34", "│") + (math.floor(formats[j].attributes["format_display_size"] - 1) * " "), end="")
                    
        else:
            for guess in formats:
                format_display_size = guess.attributes["format_display_size"]
                
                find_slash = guess.file_type.value.find("/")
                find_slash = find_slash if find_slash != None else guess.file_type.value.find("$")
                find_slash = find_slash if find_slash != None else 0
                            
                print(sgr("1", math.floor(format_display_size) * str(guess.file_type.value[find_slash+1])), end="")
    print()
