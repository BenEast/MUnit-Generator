from collections import OrderedDict

###########################
# Author: Benjamin East
# Last Updated: 06/25/2017
###########################

# A custom class of (str, OrderedDict) pairs; made to map XML tags and attributes to.
class TagPair:
    # Initialize a new str, OrderedDict TagPair.
    # Can raise a TypeError if an incorrect type is given.
    def __init__(self, tag : str, attributes : OrderedDict) -> None:
        if isinstance(tag, str) and isinstance(attributes, OrderedDict):
            self._tag = tag
            self._attributes = attributes
        else:
            raise TypeError('Invalid types passed to TagPair __init__')
    
    # Delete the TagPair.
    def __del__(self) -> None:
        del self._tag
        del self._attributes
    
    # Returns true if other == self, and false otherwise.
    def __eq__(self, other) -> bool:
        if not isinstance(other, TagPair):
            return False
        if self._tag != other.getTag():
            return False
        if len(self._attributes) != len(other.getAttributes()):
            return False
        for key in self._attributes.keys():
            if not key in other.getAttributes():
                return False
            else:
                if self._attributes.get(key) != other.getAttributes().get(key):
                    return False
        return True
    
    # Returns true if other != self and false otherwise.    
    def __ne__(self, other) -> bool: 
        return not self.__eq__(other)
                
    # Return a string representation of the TagPair.
    def __str__(self) -> str:
        return 'TagPair\t (' + str(self._tag) + ' : ' + str(self._attributes) + ')'

    # Returns the tag of this pair.
    def getTag(self) -> str:
        return self._tag
    
    # Sets the tag of this pair to newTag.
    # Can raise a TypeError if an incorrect type is given.
    def setTag(self, newTag : str) -> None:
        if isinstance(newTag, str):
            self._tag = newTag
        else:
            raise TypeError('Non-str passed to TagPair setTag')
    
    # Returns the attributes OrderedDict of this pair.
    def getAttributes(self) -> OrderedDict:
        return self._attributes

    # Sets the attributes of this pair to newAttributes.
    # Can raise a TypeError if an incorrect type is given.
    def setAttributes(self, newAttributes : OrderedDict) -> None:
        if isinstance(newAttributes, OrderedDict):
            self._attributes = newAttributes
        else:
            raise TypeError('Non-OrderedDict passed to TagPair setAttributes')
    
    # Returns the value of attributeName if it is present, and None otherwise.
    def getAttribute(self, attributeName : str) -> str: 
        if attributeName in self._attributes:
            return self._attributes[attributeName]
        else:
            return None
    
    # Sets an attribute key:value pair of attributeName:attributeValue.
    # Overwrites an existing attribute of the same name.
    # Can raise a TypeError if an incorrect type is given.
    def setAttribute(self, attributeName : str, attributeValue : str) -> None:
        if isinstance(attributeName, str) and isinstance(attributeValue, str):
            self._attributes[attributeName] = attributeValue
        else:
            raise TypeError('Invalid parameter types passed to TagPair setAttribute')

    # Removes an attribute from the _attributes OrderedDict if a key of attributeName exists.
    def removeAttribute(self, attributeName : str) -> None:
        if attributeName in self._attributes:
            self._attributes.pop(attributeName, None)
