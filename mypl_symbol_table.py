"""MyPL SymbolTable implementation.

NAME: S. Bowers
DATE: Spring 2024
CLASS: CPSC 326

"""



class SymbolTable:

    def __init__(self):
        """Create an empty symbol table."""
        self.environments = []

        
    def __len__(self):
        """Returns number of environments in symbol table."""
        return len(self.environments)


    def __repr__(self):
        """Returns a string representation of the environments."""
        return str(self.environments)

    
    def push_environment(self):
        """Add a new environment to the symbol table."""
        self.environments.append({})

        
    def pop_environment(self):
        """Remove the most recently added environment from the symbol table.

        """
        if self.environments:
            self.environments.pop()


    def add(self, name, info):
        """Add a name and its info to the current environment.
        
        Args:
            name -- The name to add.
            info -- The info to associate to the name.
        """
        if self.environments:
            self.environments[-1][name] = info

            
    def exists(self, name):
        """True if the name exists in an environment in the symbol table.
        
        Args:
            name: The name to search for.

        """
        for i in range(1, len(self)+1): 
            if name in self.environments[-i]:
                return True
        return False

    
    def exists_in_curr_env(self, name):
        """True if the name exists in the current (most recently added)
        environment.

        Args:
            name: The name to search for.

        """
        return self.environments and name in self.environments[-1]

    
    def get(self, name):
        """Return the info for a given name. Checks environments for name from
        most recent to least recent.

        Args:
            name: The name whose info is to be returned.

        """
        n = len(self)
        for i in range(1, len(self)+1):
            if name in self.environments[-i]:
                return self.environments[-i][name]
        return None

    
