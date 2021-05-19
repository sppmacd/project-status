from .guessers import FileGuess

class FileTypeGuesser:
    def guess(self, file):
        return FileGuess()

class DetectorRegistry:
    instance = None
    
    def __init__(self):
        if DetectorRegistry.instance == None:
            DetectorRegistry.instance = self
        else:
            raise AssertionError("Double singleton")
        
        self.file_type_guessers = []
        
    def register_file_type_guesser(self, guesser):
        self.file_type_guessers.append(guesser)
        
    def guess_file_type(self, file):
        matching_guesses = []
        for guesser in self.file_type_guessers:
            guess = guesser.guess(file)
            if guess != None:
                matching_guesses += guess
                
        if len(matching_guesses) == 0:
            print("Couldn't guess file type: " + file.path)
        
        return matching_guesses

from .guessers import *
DetectorRegistry()
register_all_guessers(DetectorRegistry.instance)
    
