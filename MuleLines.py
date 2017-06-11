import shlex
from collections import OrderedDict

class MuleLines:
    MULE_TAG_EQUIVALENTS = {'<flow' : '<munit-test', '<sub-flow' : '<munit-test',
                            '<set-payload' : '<munit:set payload', '<flow-ref' : '<flow-ref', 
                            '<set-variable' : '<munit:set variable', '</flow>' : '</munit:test>',
                            '</sub-flow>' : '</munit:test>', '</mule>' : '</mule>'}
    
    def __init__(self):
        self._muleDict = OrderedDict()
        
    def createMuleDict(self, lines):
        for line in lines:
            if line[0] == '<' and not line[1] == '?':
                splitLine = shlex.split(line) # Preserves spaces inside quoted strings
                self._muleDict[splitLine[0].lower()] = dict()
                if len(splitLine) > 1:
                    for item in splitLine[1:]:
                        attrAndValue = item.split('=')
                        (self._muleDict[splitLine[0]])[attrAndValue[0]] = attrAndValue[1]
    
    def createMUnitDict(self):
        # Vars to monitor position during parsing
        inFlow = False
        inChoice = False
        mUnitDict = OrderedDict()
        
        for key in self._muleDict:
            if key == '<flow' or key == '<sub-flow':
                inFlow = True
            elif key == '</flow>' or key == '</sub-flow>':
                inFlow = False
            elif key == '<choice':
                inChoice = True
            elif key == '</choice>':
                inChoice = False
            
            mUnitKey = self.MULE_TAG_EQUIVALENTS.get(key)
            if mUnitKey:
                mUnitDict[mUnitKey] = dict()
            else:
                continue
            
        return mUnitDict
        
    def getTags(self):
        return self._muleDict.keys()
    
    def getAttributes(self, tag):
        return self._muleDict.get(tag).keys()
    
    def getAttributesAndValues(self, tag):
        return self._muleDict.get(tag)
    
    def toString(self):
        output = '{'
        for key in self._muleDict.keys():
            output += '(' + key + ': ' + str(self._muleDict.get(key)) + ')'
            
        return output + '}'
    