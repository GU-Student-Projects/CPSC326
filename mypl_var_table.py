"""MyPL Variable Table for managing variable to offset mappings during
code generation.

NAME: S. Bowers
DATE: Spring 2024
CLASS: CPSC 326

"""

class VarTable:

    def __init__(self):
        """Create an empty var table"""
        self.environments = []
        self.total_vars = 0
        
        
    def __len__(self):
        """Returns the number of environments in the symbol table."""
        return len(self.environments)


    def __repr__(self):
        """Returns a string representation of the environments."""
        return str(self.environments)

    
    def push_environment(self):
        """Add a new environment to the symbol table."""
        self.environments.append([])

        
    def pop_environment(self):
        """Remove the most recently added environment from the symbol table.

        """
        if self.environments:
            self.total_vars -= len(self.environments[-1])
            self.environments.pop()

            
    def add(self, var_name):
        """Add a variable to the table in the current environment.
        
        Args: 
            var_name -- The variable name to add.

        """
        if self.environments:
            self.environments[-1].append(var_name)
            self.total_vars += 1
            
            
    def get(self, var_name):
        """Returns the offset of the variable if it is in the table. Returns
        None if the variable name is not in the table.

        Args:
            var_name -- The variable to lookup in the table.

        """
        num_remaining = self.total_vars
        for i in range(1, len(self) + 1):
            num_remaining -= len(self.environments[-i])
            if var_name in self.environments[-i]:
                return num_remaining + self.environments[-i].index(var_name)
        return None

    
