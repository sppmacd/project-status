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
        
    def register_file_type_guesser(self, name, guesser, **kwargs):
        guesser.name = name
        priority = kwargs.get("priority")
        priority = priority if priority != None else 0
        if not priority in self.file_type_guessers:
            self.file_type_guessers[priority] = []
        self.file_type_guessers[priority].append(guesser)
        
    def guess_file_type(self, file):
        matching_guesses = []
        type_classes = set()
        
        """
        If the file has multiple guesses, just one need to be in include/exclude list
        # to be included/excluded.
        """
        for guesser_list in self.file_type_guessers.values():
            for guesser in guesser_list:
                # Exclude/include
                if "/" + guesser.name in config.args.exclude:
                    continue

                if len(config.args.include) > 0 and not "/" + guesser.name in config.args.include:
                    continue
                
                # Actual guess
                guess = guesser.guess(file)
                if guess != None:
                    guess_added = []
                    for one_guess in guess:
                        one_guess.guesser = guesser.name
                        try:
                            one_guess.attributes["file_size"] = os.path.getsize(file.path)
                        except:
                            one_guess.attributes["file_size"] = 0
                            
                        if not one_guess.file_type.clazz in type_classes:
                            type_classes.add(one_guess.file_type.clazz)
                            guess_added.append(one_guess)
                        
                    matching_guesses += guess_added
                    
        if len(matching_guesses) == 0:
            print_verbose("Couldn't guess file type: " + file.path)
        
        return matching_guesses

from .guessers import *
DetectorRegistry()
register_all_guessers(DetectorRegistry.instance)
    
