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

def fancy_display(data, attribute, **kwargs):
    
    # Count total attribute value.
    total_attribute_value = 0
    for guess in data:
        attribute_value = guess.attributes.get(attribute)
        total_attribute_value += (attribute_value if attribute_value != None else 0)
    
    # Do not display anything if no data
    if total_attribute_value == 0:
        print(sgr("1;31", "\n (No data)\n"))
        return
        
    # TODO: Detect terminal size
    # TODO: Display other guesses as "Other" category
    display_size = 100
    total_line_count = 0
    
    # Generate display size for each guess
    for guess in data:
        attribute_value = guess.attributes.get(attribute)
        attribute_value = attribute_value if attribute_value != None else 0
        format_display_size = int(attribute_value * display_size / total_attribute_value)
        guess.attributes["format_display_size"] = format_display_size

    # Print list of guesses
    print()
    
    for guess in reversed(data):
        if guess.attributes.get(attribute) != None:
            print(" •", guess.file_type.to_fancy_string() + " - " + sgr("1", str(guess.attributes.get(attribute))) + " " + kwargs.get("description"))
    
    # Print fancy chart :)
    print()

    # Labels
    for i in range(len(data)):
        attribute_value = data[i].attributes.get(attribute)
        attribute_value = attribute_value if attribute_value != None else 0
        
        if data[i].attributes["format_display_size"] > 0:  
            print("    ", end="")
                    
        for j in range(i):
            if data[i].attributes["format_display_size"] > 0 and data[j].attributes["format_display_size"] > 0:  
                sgr_val = "38;2;" + str(HSV(colors[j % len(colors)], 0.5, 0.8).to_rgb())
                print(sgr(sgr_val, "│") + (math.floor(data[j].attributes["format_display_size"] - 1) * " "), end="")
        
        if data[i].attributes["format_display_size"] > 0:  
            sgr_val = "38;2;" + str(HSV(colors[i % len(colors)], 0.5, 0.8).to_rgb())
            print(sgr(sgr_val, "╭─── ") + data[i].file_type.to_fancy_string() + " - " + sgr("1", str(attribute_value * 100 // total_attribute_value)) + "%")
                    
    # Last lines
    print("    ", end="")
    for j in range(len(data)):
        if data[j].attributes["format_display_size"] > 0:
            sgr_val = "38;2;" + str(HSV(colors[j % len(colors)], 0.5, 0.8).to_rgb())
            spaces = math.floor(data[j].attributes["format_display_size"] - 1) * " "
            print(sgr(sgr_val, "│" + spaces), end="")
    
    # The chart itself
    print("\n    ", end="")
    
    color = 0
    total_format_display_size = 0
    for guess in data:
        format_display_size = guess.attributes["format_display_size"]

        range_val = math.floor(format_display_size)
        for i in range(range_val):
            v = ((((i / range_val) - 0.5) * 2)**2/2)/2 + 0.6
            print(sgr("1;38;2;" + str(HSV(colors[color % len(colors)], 0.5, v).to_rgb()), "▀"), end="")

        color += 1
        total_format_display_size += format_display_size
    
    other_display_size = display_size - total_format_display_size
    for i in range(other_display_size):
        v = ((((i / other_display_size) - 0.5) * 2)**2/2)/2 + 0.6
        print(sgr("1;38;2;" + str(HSV(colors[color % len(colors)], 0, v).to_rgb()), "▀"), end="")
    
    print("\n")

def directory_fancy_display(dir):
    global colors
    
    # FIXME: Multiple accesses to attribute list!!!
    build_systems = []
    cis = []
    formats = []
    version_control = []
    
    def compare_guesses(guess):
        return guess.file_type.value
    
    def compare_guesses_by_attribute(guess, attribute):
        attribute = guess.attributes.get(attribute)
        return attribute if attribute != None else 0
    
    for guess in dir.collapsed_guesses():
        if guess.file_type.clazz == "$build":
            build_systems.append(guess)
        elif guess.file_type.clazz == "$ci":
            cis.append(guess)
        elif guess.file_type.clazz == "$mime":
            formats.append(guess)
        elif guess.file_type.clazz == "$version":
            version_control.append(guess)
        else:
            print_error("Unknown class: " + guess.file_type.clazz)

    build_systems.sort(key=compare_guesses)
    cis.sort(key=compare_guesses)
    formats_by_storage = sorted(formats, key=lambda guess : compare_guesses_by_attribute(guess, "file_size"))
    formats.sort(key=lambda guess : compare_guesses_by_attribute(guess, "lines_of_code"))
    
    def print_header(text):
        print("   -- " + sgr("1", text) + " --")
    
    print()
    print_header("General")
    print()
    print(" • Version Control: ", end="")
    for guess in version_control:
        print(guess.file_type.to_fancy_string(), end=", ")
    print()
    
    print(" • Continuous Integration: ", end="")
    for guess in cis:
        print(guess.file_type.to_fancy_string(), end=", ")
    print("\n")
    
    print_header("Storage")
    fancy_display(formats_by_storage, "file_size", description="bytes")
    
    print_header("Build systems")
    fancy_display(build_systems, "file_count", description="config file(s)")
    
    print_header("Code")
    fancy_display(formats, "lines_of_code", description="line(s) of code")
