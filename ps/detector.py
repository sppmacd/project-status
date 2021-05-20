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
        
        self.file_type_guessers = {}
        
    def register_file_type_guesser(self, name, guesser):
        self.file_type_guessers[name] = guesser
        
    def guess_file_type(self, file):
        matching_guesses = []
        for name, guesser in self.file_type_guessers.items():
            if "/" + name in config.args.exclude:
                continue
            guess = guesser.guess(file)
            if guess != None:
                for one_guess in guess:
                    one_guess.guesser = name
                matching_guesses += guess
                
        if len(matching_guesses) == 0:
            print_verbose("Couldn't guess file type: " + file.path)
        
        return matching_guesses

from .guessers import *
DetectorRegistry()
register_all_guessers(DetectorRegistry.instance)
    
