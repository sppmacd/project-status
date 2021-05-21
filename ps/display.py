import config as config
import math

from .logging import *
from .guessers import FileGuess, FileType

colors = []

class RGB:
    def __init__(self,r,g,b):
        self.r=r # 0-1
        self.g=g # 0-1
        self.b=b # 0-1
        
    def __repr__(self):
        return str(int(self.r*255)) + ";" + str(int(self.g*255)) + ";" + str(int(self.b*255))

class HSV:
    def __init__(self,h,s,v):
        self.h=h # 0-360
        self.s=s # 0-1
        self.v=v # 0-1

    def to_rgb(self):
        C = self.v * self.s
        Hp = int(self.h) / 60
        X = C * (1 - abs(Hp % 2 - 1))

        if Hp >= 0 and Hp <= 1:
            rgb1 = (C, X, 0)
        elif Hp > 1 and Hp <= 2:
            rgb1 = (X, C, 0)
        elif Hp > 2 and Hp <= 3:
            rgb1 = (0, C, X)
        elif Hp > 3 and Hp <= 4:
            rgb1 = (0, X, C)
        elif Hp > 4 and Hp <= 5:
            rgb1 = (X, 0, C)
        elif Hp > 5 and Hp <= 6:
            rgb1 = (C, 0, X)
            
        m = self.v - C
        return RGB(rgb1[0] + m, rgb1[1] + m, rgb1[2] + m)
        

def generate_hsv_lookup_table(count):
    for i in range(count):
        colors.append(i * 360 / count)

generate_hsv_lookup_table(9)

def directory_fancy_display(dir):
    global colors
    
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
    # TODO: Display other guesses as "Other" category
    display_size = 100
    total_line_count = 0
    
    for guess in formats:
        lines_of_code = guess.lines_of_code()
        lines_of_code = lines_of_code if lines_of_code != None else 0
        format_display_size = int(lines_of_code * display_size / total_lines_of_code)
        guess.attributes["format_display_size"] = format_display_size

    print()
    
    for guess in formats:
        if guess.lines_of_code() != None:
            print(" •", guess.file_type.to_fancy_string() + " - " + sgr("1", str(guess.lines_of_code())) + " lines of code")
    print()

    for i in range(len(formats) + 1):
    
        if i < len(formats):
            space_drawn = False
            for j in range(i + 1):
                if int(formats[j].attributes["format_display_size"]) > 0:
                    if not space_drawn:
                        print("    ", end="")
                        space_drawn = True

                    sgr_val = "38;2;" + str(HSV(colors[j % len(colors)], 0.5, 0.8).to_rgb())
                    if j == i:
                        print(sgr(sgr_val, "┌─ ") + formats[j].file_type.to_fancy_string() + " - " + sgr("1", str(formats[j].lines_of_code() * 100 // total_lines_of_code)) + "%")
                    else:
                        print(sgr(sgr_val, "│") + (math.floor(formats[j].attributes["format_display_size"] - 1) * " "), end="")
                    
        else:
            print("    ", end="")
            for j in range(i):
                if int(formats[j].attributes["format_display_size"]) > 0:
                    sgr_val = "38;2;" + str(HSV(colors[j % len(colors)], 0.5, 0.8).to_rgb())
                    print(sgr(sgr_val, "│") + (math.floor(formats[j].attributes["format_display_size"] - 1) * " "), end="")
            
            print("\n    ", end="")
            
            color = 0
            for guess in formats:
                format_display_size = guess.attributes["format_display_size"]

                range_val = math.floor(format_display_size)
                for i in range(range_val):
                    v = ((((i / range_val) - 0.5) * 2)**2/2)/2 + 0.6
                    print(sgr("1;38;2;" + str(HSV(colors[color % len(colors)], 0.5, v).to_rgb()), "▀"), end="")

                color += 1
    print()
