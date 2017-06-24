import shlex
import sys

from collections import OrderedDict
from TagList import TagList
from TagPair import TagPair

###########################
# Author: Benjamin East
# Last Updated: 06/23/2017
###########################

# A custom class to parse lines of Mule code and generate mUnit tests based on
# a pre-existing base of XML Mule code.
class MuleLines:
    # Initialize TagList objects for existing Mule code and MUnit code to be generated.
    def __init__(self):
        self._muleTagList = TagList()
        self._mUnitTagList = TagList()
    
    # Parse XML lines of Mule code into the _muleTagList for this object.
    def parseMuleFileLines(self, lines : []) -> None:
        for line in lines:
            # Take tagged lines that are not lists of Mule dependencies
            if line[0] == '<' and not line[1] == '?':
                splitLine = shlex.split(line)  # Split the line; preserves spaces in quoted strings.
                # If the XML tag has additional attributes, map them to an OrderedDict
                if len(splitLine) > 1:
                    attrDict = OrderedDict()
                    if splitLine[0] == '<mule':  # Add close at end tag for 1st mule tag--- it wasn't populating previously
                        attrDict['closeAtEnd'] = False
                    for item in splitLine[1:]:  # Skip the tag in the line
                        item.lower()
                        attrAndValue = item.split('=')
                        if attrAndValue[1][-2:] == '/>':
                            attrDict['closeAtEnd'] = True
                            attrDict[attrAndValue[0]] = attrAndValue[1][:-2]
                        elif attrAndValue[1][-1:] == '>':
                            attrDict['closeAtEnd'] = False
                            attrDict[attrAndValue[0]] = attrAndValue[1][:-1]
                        else:
                            attrDict[attrAndValue[0]] = attrAndValue[1]
                    self._muleTagList.append(TagPair(splitLine[0].lower().strip('<'), attrDict))
                else:
                    attrDict = OrderedDict()
                    if splitLine[0][:2] == '</':
                        attrDict['closeAtEnd'] = False
                    else:
                        attrDict['closeAtEnd'] = True
                    self._muleTagList.append(TagPair(splitLine[0].lower().strip('<').strip('>'), attrDict))
    
    # Extracts operations performed in a choice block in the provided flow.
    # Returns a TagList containing the choice operations.
    # Can raise a TypeError if an incorrect parameter type is provided.
    def _extractChoiceOperations(self, flowTagList : TagList) -> TagList:
        if not isinstance(flowTagList, TagList):
            raise TypeError('Invalid parameter type passed to MuleLines _extractChoiceOperations')
        choiceOperations = TagList()
        inChoiceClause = False
        for pair in flowTagList.pairs():
            if pair.getTag() == 'when' or pair.getTag() == 'otherwise':
                inChoiceClause = True
            elif pair.getTag() == '/when' or pair.getTag() == '/otherwise':
                inChoiceClause = False
            elif inChoiceClause:
                choiceOperations.append(pair)
        return choiceOperations
    
    # Iterates through the muleTagList and returns a list of TagLists, where each
    # returned TagList is a mule flow.
    def _isolateFlows(self) -> []:
        flows = []
        inFlow = False
        outputList = TagList()
        for pair in self._muleTagList.pairs():
            # If within a flow or sub-flow block, add the pair to the outputList
            if pair.getTag() == 'flow' or pair.getTag() == 'sub-flow':
                inFlow = True
                outputList.append(pair)
            elif pair.getTag() == '/flow' or pair.getTag() == '/sub-flow':
                outputList.append(pair)
                flows.append(outputList.copy())
                # Clear the outputList in case another flow is present later
                outputList.clear()
                inFlow = False
            elif inFlow:
                outputList.append(pair)
        return flows
    
    # Generates MUnit Test Flows given the operations performed in a choice block, 
    # and a TagList of a flow containing a choicePlaceholder tag.
    # Can raise a type error if invalid parameter types are provided.
    def _generateMUnitChoiceTestFlows(self, choiceOperations : TagList,
                                      mUnitBaseTagList : TagList) -> []:
        if not isinstance(choiceOperations, TagList) or not isinstance(mUnitBaseTagList, TagList):
            raise TypeError('Invalid parameter types passed to MuleLines _generateMUnitChoiceTestFlows')
        outputFlows = []
        testCount = 1
        # Create a flow for each choice operation. (Later support should include multiple operations)
        for choiceOp in choiceOperations.pairs():
            for pair in mUnitBaseTagList.pairs():
                if pair.getTag() == 'choicePlaceholder':
                    # replace placeholder with choiceOperation
                    pair.setTag(choiceOp.getTag())
                    pair.setAttributes(choiceOp.getAttributes())
                elif pair.getTag() == 'munit:test':
                    if 'name' in pair.getAttributes():
                        # Update test name attribute
                        name = str(pair.getAttributes().get('name'))
                        pair.setAttribute('name', name + '-' + str(testCount))
                    else:
                        pair.setAttribute('name', 'MUnitTestFlow-' + str(testCount))
            # Add test count number as applicable        
            testCount = testCount + 1
            outputFlows.append(mUnitBaseTagList)     
        return outputFlows
    
    # Replace choice blocks in the mule TagList with a choice placeholder.
    # Can raise a TypeError if incorrect parameter types are provided.
    def _replaceChoiceBlocks(self, muleTagList : TagList) -> TagList:
        if not isinstance(muleTagList, TagList):
            raise TypeError('Invalid parameter passed to MuleLines _replaceChoiceBlocks')
        inChoiceBlock = False
        for pair in muleTagList.pairs():
            # Determine the edges of the choice block, and remove everything in between.
            if pair.getTag() == 'choice':
                inChoiceBlock = True
            elif pair.getTag() == '/choice':
                inChoiceBlock = False
                pair.setTag('choicePlaceholder')  
            if inChoiceBlock:
                muleTagList.remove(pair)
        return muleTagList
    
    # Convert a TagList of mule code to a TagList of MUnit code.
    # Can raise a TypeError if incorrect parameter types are provided.
    def _convertMuletoMUnit(self, muleTagList : TagList) -> TagList:
        if not isinstance(muleTagList, TagList):
            raise TypeError('Invalid parameter passed to MuleLines _convertMuletoMUnit')
        self._replaceChoiceBlocks(muleTagList)  # Replace choice blocks with choicePlaceholder
        mUnitTagList = TagList()
        # Iterate through the Mule XML tags and attributes to create MUnit tags and attributes.
        for pair in muleTagList.pairs():
            muleAttributes = pair.getAttributes()  # Attributes for the given Mule XML tag
            mUnitAttributes = OrderedDict()  # Holder for MUnit attributes if they are created
            mUnitAttributes['closeAtEnd'] = muleAttributes.get('closeAtEnd')  # Pass closeAtEnd for final output parsing
            
            if pair.getTag() == 'flow' or pair.getTag() == 'sub-flow':
                if 'name' in muleAttributes:
                    mUnitAttributes['name'] = str(muleAttributes.get('name')) + '_test'
                mUnitTagList.append(TagPair('munit:test', mUnitAttributes)) 
                   
            elif pair.getTag() == '/flow' or pair.getTag() == '/sub-flow':
                mUnitTagList.append(TagPair('/munit:test', mUnitAttributes))  
                    
            elif pair.getTag() == 'choicePlaceholder':
                mUnitTagList.append(pair)
                
            elif pair.getTag() == 'set-payload':
                mUnitAttributes['payload'] = muleAttributes.get('value')
                if 'doc:name' in muleAttributes:
                    mUnitAttributes['doc:name'] = muleAttributes.get('doc:name')
                mUnitTagList.append(TagPair('munit:set', mUnitAttributes))  
                
            elif pair.getTag() == 'set-variable':
                mUnitAttributes['variable'] = muleAttributes.get('value')
                mUnitTagList.append(TagPair('munit:set', mUnitAttributes))
                
            elif pair.getTag() == 'flow-ref':  # Will likely want to change to mock verify call
                if 'name' in muleAttributes:
                    mUnitAttributes['name'] = muleAttributes.get('name')
                elif 'doc:name' in muleAttributes:
                    mUnitAttributes['doc:name'] = muleAttributes.get('doc:name')
                mUnitTagList.append(TagPair('flow-ref', mUnitAttributes))
                
            elif pair.getTag() == '/mule':
                mUnitTagList.append(TagPair('/mule', mUnitAttributes))
        return mUnitTagList
    
    # Create an MUnit TagList by parsing the Mule XML tags and properties from the TagList.        
    def createMUnitTests(self) -> None:
        # Flows is an array of TagLists, where each TagList is a mule flow
        flows = self._isolateFlows()
        for flow in flows:
            # Isolate the operations performed in the mule choice blocks
            mUnitChoiceOperations = self._convertMuletoMUnit(self._extractChoiceOperations(flow))
            # Generate the mUnit version of the code
            mUnitFlow = self._convertMuletoMUnit(flow)
            # Generate multiple test flows if a choice block is present
            if mUnitFlow.containsTag('choicePlaceholder'):
                testFlows = self._generateMUnitChoiceTestFlows(mUnitChoiceOperations, mUnitFlow)
                for flow in testFlows:
                    for pair in flow.pairs():
                        self._mUnitTagList.append(pair)
            # Otherwise, create a single test flow
            else:
                for pair in mUnitFlow.pairs():
                    self._mUnitTagList.append(pair)

    # Converts the mUnitTagList to XML code and writes it to the provided outputFilePath.
    def createMUnitSuiteFile(self, outputFilePath : str) -> None:
        if self._mUnitTagList.isEmpty():
            print('Unable to write to file; no tests available.')
            print('Parse file lines using MuleLines.parseMuleFileLines(fileLines).')
            print('Call MuleLines.createMUnitTests() to create the MUnit Tests for the file.')
        else:
            try:
                file = open(outputFilePath, 'a+')
            except IOError as error:
                print(error.error())
                print('Please input a valid output file path.')
                return
            except:
                print('Unexpected error:', sys.exc_info()[0])
                raise
                return
            
            tagDepth = 0
            # Iterate through the TagPairs, create MUnit lines, and write them to the file.
            for pair in self._mUnitTagList.pairs():
                closeAtEnd = pair.getAttribute('closeAtEnd')
                # Determine the indentation of current XML tag based on when blocks close
                if pair.getTag()[0] == '/':
                    tagDepth -= 1
                elif not closeAtEnd:
                    tagDepth += 1
                
                # Create the MUnit file lines and write them to the output file
                mUnitLine = '<' + pair.getTag()
                attributes = pair.getAttributes()
                for attribute in attributes:
                    if not attribute == 'closeAtEnd':
                        mUnitLine = mUnitLine + ' ' + attribute + '="' + attributes.get(attribute) + '"'
                if closeAtEnd:
                    mUnitLine = mUnitLine + '/>\n'
                else:
                    mUnitLine = mUnitLine + '>\n'
                file.write('\t' * tagDepth + mUnitLine)
            file.close()
