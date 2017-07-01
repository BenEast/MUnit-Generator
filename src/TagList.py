from TagPair import TagPair

###########################
# Author: Benjamin East
# Last Updated: 06/25/2017
###########################
        
# A custom class to act as an ordered list of XML tags, paired with an OrderedDict of the
# attributes of those XML tags.
class TagList:
    # Initialize as an empty list.
    def __init__(self) -> None:
        self._list = [] 
    
    # Delete the TagList.
    def __del__(self) -> None:
        del self._list
        
    # Returns true if self == other and false otherwise.
    def __eq__(self, other) -> bool:
        if not isinstance(other, TagList):
            return False
        if len(self._list) != len(other._list):
            return False
        for i in range(0, len(self._list)):
            if self._list[i] != other._list[i]:
                return False
            
        return True    
    
    # Returns true if self != other and false otherwise.
    def __ne__(self, other) -> bool:
        return not self.__eq__(other)

    # Returns a string output for the TagList.
    def __str__(self) -> str:
        output = '--- TagList ---\n'
        for pair in self._list:
            output += str(pair) + '\n'
        output += '---------------'
        
        return output
    
    # Inserts a TagPair into the TagList.
    # Can raise a TypeError if an incorrect type is given.
    def append(self, pair : TagPair) -> None:
        if isinstance(pair, TagPair):
            self._list.append(pair)
        else:
            raise TypeError('Non-TagPair passed to TagList append')
    
    # Removes everything from the TagList.
    def clear(self) -> None:
        self._list.clear()

    # Returns true if the targetPair is present in the TagList, and false otherwise.
    # Can raise a TypeError if an incorrect type is given.
    def contains(self, targetPair : TagPair) -> bool:
        if isinstance(targetPair, TagPair):
            if targetPair in self._list:
                return True
            else:
                return False
        else:
            raise TypeError('Non-TagPair passed to TagList contains')
    
    # Returns true if a TagPair with the tag is in the TagList, and false otherwise.
    def containsTag(self, tag : str) -> bool:
        for pair in self._list:
            if pair.getTag() == tag:
                return True
            
        return False
        
    # Returns an exact copy of the list that it was provided,  
    def copy(self):
        outputList = TagList()
        for pair in self._list:
            outputList.append(pair)
            
        return outputList
                        
    # Returns the first pair with a matching tag in the TagList
    def getPair(self, tag : str) -> TagPair:
        for pair in self._list:
            if pair.getTag() == tag:
                return pair
            
        return None

    # Returns the index of the first occurence of targetPair in the TagList or None if not present.
    def index(self, targetPair : TagPair) -> int:
        if not targetPair in self._list:
            return None
        
        for pair in self._list:
            if pair == targetPair:
                return self._list.index(pair)

    # Inserts the TagPair value at the provided index in the list.
    # Can raise a TypeError if an incorrect type is given.
    def insertAtIndex(self, index : int, value : TagPair) -> None:
        if isinstance(index, int) and isinstance(value, TagPair):
            self._list.insert(index, value)
        else:
            raise TypeError('Invalid types passed to TagList insertAtIndex')
    
    # Returns true if the TagList is empty, and false otherwise.
    def isEmpty(self) -> bool:
        return len(self._list) == 0
    
    # Return all of the XML tag, OrderedDict pairs
    def pairs(self) -> []:
        return [x for x in self._list]

    # Remove a pair from the TagList.
    # This will remove the first occurence that matches the pair.
    def remove(self, targetPair : TagPair) -> None:
        if not targetPair in self._list or not isinstance(targetPair, TagPair):
            return
        self._list.remove(targetPair)

    # Removes all occurences of targetPair from the TagList.
    def removeAll(self, targetPair : TagPair) -> None:
        if not targetPair in self._list or not isinstance(targetPair, TagPair):
            return
        while targetPair in self._list:
            self._list.remove(targetPair)

    # Return a list of the XML tags in the TagList    
    def tags(self) -> []:
        return [x.getTag() for x in self._list]
