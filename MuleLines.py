import shlex
from collections import OrderedDict
from TagList import TagList

###########################
# Author: Benjamin East
# Last Updated: 06/17/2017
###########################

# A custom class to parse lines of Mule code and generate mUnit tests based on
# a pre-existing base of code.
class MuleLines:
    # Initialize TagList objects for existing Mule code and MUnit code to be generated.
    def __init__(self):
        self._muleDict = TagList()
        self._mUnitDict = TagList()
    
    # Parse XML lines of Mule code into a TagList object.
    def createMuleDict(self, lines):
        for line in lines:
            # Take tagged lines that are not lists of Mule dependencies
            if line[0] == '<' and not line[1] == '?':
                splitLine = shlex.split(line)  # Split the line; preserves spaces in quoted strings.
                # If the XML tag has additional attributes, map them to an OrderedDict
                if len(splitLine) > 1:
                    attrDict = OrderedDict()
                    for item in splitLine[1:]:  # Skip the tag in the line
                        attrAndValue = item.split('=')
                        attrDict[attrAndValue[0]] = attrAndValue[1].strip('/>')
                    self._muleDict.insert((splitLine[0].lower(), attrDict))
                else:
                    self._muleDict.insert((splitLine[0], None))
        self._calculateTestNumbers()
    
    # Parses the TagList of Mule code to determine how many tests are needed based on choice blocks.
    # Adds an additional attribute 'numTests' to flow and sub-flow tags in the mule TagList
    def _calculateTestNumbers(self):
        clonedList = TagList.clone(self._muleDict)
        testsNeeded = 1
        currentFlowPair = None
        for pair in clonedList.pairs(): 
            # Take action on certain tags below; where pair[0] is the Mule XML tag.
            if pair[0] == '<flow':
                currentFlowPair = pair
                
            elif pair[0] == '<sub-flow':
                currentFlowPair = pair
                
            elif pair[0] == '<when':
                testsNeeded = testsNeeded + 1
                
            elif pair[0] == '<otherwise':
                testsNeeded = testsNeeded + 1
                
            elif pair[0] == '</flow>':
                # Apply choiceOptions as numTests attribute for the current flow
                self._muleDict.addAttributeToPair(currentFlowPair, 'numTests', testsNeeded)
                testsNeeded = 1
                currentFlowPair = None
                
            elif pair[0] == '</sub-flow>':
                # Apply choiceOptions as numTests attribute for the current flow
                self._muleDict.addAttributeToPair(currentFlowPair, 'numTests', testsNeeded)
                testsNeeded = 1
                currentFlowPair = None
                
            clonedList.remove(pair)
    
    # Create an MUnit TagList by parsing the Mule XML tags and properties from the TagList.
    # This creates the main body of the MUnit XML file.           
    def createMUnitDict(self):
        # Vars to monitor position during parsing
        testCount = 0
        muleDictClone = TagList.clone(self._muleDict)
        self._mUnitDict = TagList()
        
        # Iterate through the Mule XML tags and attributes to create MUnit tags and attributes.
        for pair in muleDictClone.pairs():
            muleAttributes = pair[1] # Attributes for the given Mule XML tag
            mUnitAttributes = OrderedDict() # Holder for MUnit attributes if they are created
            
            if pair[0] == '<flow':
                testCount = testCount + 1
                for key in muleAttributes.keys():
                    if key == 'name':
                        mUnitAttributes['name'] = 'doc-test-' + muleAttributes.get(key) + 'Test' + str(testCount)
                self._mUnitDict.insert(('<munit:test', mUnitAttributes))
            
            elif pair[0] == '</flow>':
                testCount = 0
                self._mUnitDict.insert(('</munit:test>', None))   
                
            elif pair[0] == '<sub-flow':
                testCount = testCount + 1
                for key in muleAttributes.keys():
                    if key == 'name':
                        mUnitAttributes['name'] = 'doc-test-' + muleAttributes.get(key) + 'Test' + str(testCount)
                self._mUnitDict.insert(('<munit:test', mUnitAttributes))
                        
            elif pair[0] == '</sub-flow>':
                testCount = 0
                self._mUnitDict.insert(('</munit:test>', None))
                    
            elif pair[0] == '<http:listener':
                continue
                
            elif pair[0] == '<set-payload':
                mUnitAttributes['payload'] = '' # MUnit payloads will be empty; users will need to specify
                for key in muleAttributes.keys():
                    if key == 'doc:name':
                        mUnitAttributes['doc:name'] = 'Set Message Payload for Test ' + str(testCount)
                self._mUnitDict.insert(('<munit:set', mUnitAttributes))
                
            elif pair[0] == '<flow-ref':  # Will likely want to change to mock verify call
                for key in muleAttributes.keys():
                    if key == 'name':
                        mUnitAttributes['name'] = muleAttributes.get('name')
                    elif key == 'doc:name':
                        mUnitAttributes['doc:name'] = muleAttributes.get('doc:name')
                self._mUnitDict.insert(('<munit:set', mUnitAttributes))
                        
            elif pair[0] == '<when':
                continue
                
            elif pair[0] == '<otherwise':
                continue
                
            elif pair[0] == '<set-variable':
                continue
                
            elif pair[0] == '</mule>':
                self._mUnitDict.insert(('</mule>', None))
            
            muleDictClone.remove(pair)
