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
        
        """
        If the file has multiple guesses, just one need to be in include/exclude list
        # to be included/excluded.
        """
        for name, guesser in self.file_type_guessers.items():
            # Exclude/include
            if "/" + name in config.args.exclude:
                continue

            if len(config.args.include) > 0 and not "/" + name in config.args.include:
                continue
            
            # Actual guess
            guess = guesser.guess(file)
            if guess != None:
                for one_guess in guess:
                    one_guess.guesser = name
                    one_guess.attributes["file_size"] = os.path.getsize(file.path)
                matching_guesses += guess
                
        if len(matching_guesses) == 0:
            print_verbose("Couldn't guess file type: " + file.path)
        
        return matching_guesses

from .guessers import *
DetectorRegistry()
register_all_guessers(DetectorRegistry.instance)
    
