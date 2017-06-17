###########################
# Author: Benjamin East
# Last Updated: 06/17/2017
###########################

# A custom class to act as an ordered list of XML tags, paired with an OrderedDict of the
# attributes of those XML tags.
# This class isn't particularly safe/stable at the moment, and was made sheerly for my needs
# in this project. It may be updated to be safer and more restrictive in the future.
class TagList:
    # Initialize as an empty list
    def __init__(self):
        self._list = [] 
    
    # Return a list of the XML tags in the TagList    
    def tags(self):
        return [x[0] for x in self._list]
    
    # Return all of the XML tag, OrderedDict pairs
    def pairs(self):
        return [x for x in self._list]
    
    # Static method to allow the cloning of a given TagList.
    # Can be called with TagList.clone(listToClone).
    # Returns an exact copy of the list that it was provided, 
    @staticmethod    
    def clone(tagList):
        outputList = TagList()
        for pair in tagList.pairs():
            outputList.insert(pair)
        return outputList
        
    # Add a new attribute to a specified pair in the list.
    def addAttributeToPair(self, targetPair, newAttrKey, newAttrVal):
        for pair in self._list:
            if pair == targetPair:
                pair[1][newAttrKey] = newAttrVal  # Where pair[1] is an OrderedDict
                break
    
    # Insert a pair to the TagList
    def insert(self, pair):
        self._list.append(pair)
    
    # Remove a pair from the TagList.
    # This will remove the first occurence that matches the pair.
    def remove(self, targetPair):
        for pair in self._list:
            if pair == targetPair:
                self._list.remove(pair)
                return    
    
    # Defines a string output for the TagList
    def __str__(self):
        output = ''
        for pair in self._list:
            output += str(pair) + '\n'
        return output[:-1] # Strip the last newline
    