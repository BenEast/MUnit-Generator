import shlex
import sys
from collections import OrderedDict
from TagList import TagList
from TagPair import TagPair

###########################
# Author: Benjamin East
# Last Updated: 06/24/2017
###########################

# A custom class to parse lines of Mule code and generate mUnit tests based on
# a pre-existing base of XML Mule code.
class MuleLines:
    # Initialize a list for original mule XML code, and two 
    # TagList objects for existing Mule code and MUnit code to be generated.
    def __init__(self):
        self._inputFileName = ""
        self._muleFileLines = []
        self._muleTagList = TagList()
        self._mUnitTagList = TagList()
        
    # Create an MUnit TagList by parsing the Mule XML tags and properties from the TagList.        
    def createMUnitTests(self) -> None:
        self._generateMUnitDependencies()
        # Flows is an array of TagLists, where each TagList is a mule flow
        flows = self._isolateFlows()
        for flow in flows:
            # Isolate the operations performed in the mule choice blocks
            mUnitChoiceOperations = self._convertMuletoMUnit(self._extractChoiceOperations(flow))
            # Generate the mUnit version of the code
            mUnitFlow = self._convertMuletoMUnit(flow)
            # Generate multiple test flows if a choice block is present
            if mUnitFlow.containsTag('choicePlaceholder'):
                testFlows = self._generateMUnitTestFlows(mUnitChoiceOperations, mUnitFlow)
                for flow in testFlows:
                    for pair in flow.pairs():
                        self._mUnitTagList.append(pair)
            # Otherwise, create a single test flow
            else:
                for pair in mUnitFlow.pairs():
                    self._mUnitTagList.append(pair)
        endMuleAttributes = OrderedDict()
        endMuleAttributes['closeAtEnd'] = False
        self._mUnitTagList.append(TagPair('/mule', endMuleAttributes))
        
    # Converts the mUnitTagList to XML code and writes it to the provided outputFilePath.
    def createMUnitSuiteFile(self, outputFilePath : str) -> None:
        if self._mUnitTagList.isEmpty():
            print('Unable to write to file; no tests available.')
            print('Parse file lines using MuleLines.parseMuleFileLines(fileLines).')
            print('Call MuleLines.createMUnitTests() to create the MUnit Tests for the file.')
        else:
            try:
                file = open(outputFilePath, 'w+')
            except IOError as error:
                print(error.error())
                print('Please input a valid output file path.')
                return
            except:
                print('Unexpected error:', sys.exc_info()[0])
                return
            # Write initial XML definition tag to file
            file.write('<?xml version="1.0" encoding="UTF-8"?>\n\n')
            tagDepth = 0
            testNumber = 1
            currentFlow = ""
            # Iterate through the TagPairs, create MUnit lines, and write them to the file.
            for pair in self._mUnitTagList.pairs():
                # Create a test number for flows with multiple test cases
                if pair.getTag() == 'munit:test': 
                    if currentFlow != pair.getAttribute('name'):
                        # Set current flow to the new flow and reset test number to 1
                        currentFlow = pair.getAttribute('name')
                        testNumber = 1
                    else:
                        testNumber += 1
                # Create the MUnit file lines and write them to the output file.
                mUnitLine = '<' + pair.getTag()
                attributes = pair.getAttributes()
                for attribute in attributes:
                    if pair.getTag() == 'munit:test' and attribute == 'name':
                        mUnitLine = (mUnitLine + ' ' + attribute + '="' + attributes.get(attribute) 
                                        + str(testNumber) + '"')
                    elif attribute != 'closeAtEnd':
                        mUnitLine = mUnitLine + ' ' + attribute + '="' + attributes.get(attribute) + '"'
                if pair.getAttribute('closeAtEnd'):
                        mUnitLine += '/>\n'
                else:
                    mUnitLine += '>\n'
                if pair.getTag() == '/munit:test':
                    mUnitLine += '\n'
                # Determine the indentation of current XML tag based on when blocks close
                if pair.getTag()[0] != '/':
                    file.write('\t' * tagDepth + mUnitLine)
                if pair.getTag()[0] == '/':
                    file.write('\t' * (tagDepth - 1) + mUnitLine)
                    tagDepth -= 1
                elif not pair.getAttribute('closeAtEnd'):
                    tagDepth += 1
            file.close()

    # Parse XML lines of Mule code into the _muleTagList for this object.
    def parseMuleFileLines(self, inputFileName : str) -> None:
        self._inputFileName = inputFileName
        self._extractMuleFileLines()
        for line in self._muleFileLines:
            if line[0] == '<' and line[1] != '?' and line[1] != '!':
                splitLine = shlex.split(line)  # Split the line; preserves spaces in quoted strings.
                # If the XML tag has additional attributes, map them to an OrderedDict
                if len(splitLine) > 1:
                    attrDict = OrderedDict()
                    for item in splitLine[1:]:  # Skip the tag in the line
                        attrAndValue = item.split('=')
                        # Add a closeAtEnd attribute, for use in writing the final output file
                        if attrAndValue[1][-2:] == '/>':
                            attrDict['closeAtEnd'] = True
                            attrDict[attrAndValue[0]] = attrAndValue[1][:-2]  # Strip closing bracket
                        elif attrAndValue[1][-1:] == '>':
                            attrDict['closeAtEnd'] = False
                            attrDict[attrAndValue[0]] = attrAndValue[1][:-1]  # Strip closing bracket
                        else:
                            attrDict[attrAndValue[0]] = attrAndValue[1]
                    self._muleTagList.append(TagPair(splitLine[0].lower().strip('<'), attrDict))
                else:  # Add a closeAtEnd attribute, for use in writing the final output file
                    attrDict = OrderedDict()
                    if splitLine[0][:2] == '</':
                        attrDict['closeAtEnd'] = False
                    else:
                        attrDict['closeAtEnd'] = True
                    self._muleTagList.append(TagPair(splitLine[0].lower().strip('<').strip('>'), attrDict))
    
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
            
            if pair.getTag() == 'flow':
                if 'name' in muleAttributes:
                    mUnitAttributes['name'] = str(muleAttributes.get('name')) + '-test-'
                    mUnitAttributes['description'] = 'Unit Test for ' + muleAttributes.get('name')
                else:
                    mUnitAttributes['name'] = 'UnitTestFlow'
                    mUnitAttributes['description'] = 'Unit Test Flow for unnamed Mule Flow'
                mUnitTagList.append(TagPair('munit:test', mUnitAttributes))       
            
            elif pair.getTag() == '/flow':
                mUnitTagList.append(TagPair('/munit:test', mUnitAttributes))       
            
            elif pair.getTag() == 'choicePlaceholder':
                mUnitTagList.append(pair)
                
            elif pair.getTag() == 'set-payload':
                mUnitAttributes['payload'] = muleAttributes.get('value')
                if 'doc:name' in muleAttributes:
                    mUnitAttributes['doc:name'] = muleAttributes.get('doc:name')
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
    
    # Reads the specified file and returns a list of file lines.
    # Splits whitespace and takes only lines beginning in tags
    def _extractMuleFileLines(self) -> None:
        with open(self._inputFileName, 'r') as file:
            self._muleFileLines = file.readlines()
        self._muleFileLines = list(filter(None, [x.lstrip(' ').strip() for x in self._muleFileLines]))
        for line in self._muleFileLines:
            if line[0] != "<":
                self._muleFileLines.remove(line)

    # Extracts all spring imports and values from the Mule TagList and adds them to the MUnit TagList
    def _extractSpringInternals(self) -> None:
        for pair in self._muleTagList.pairs():
            if ('spring' in pair.getTag() and pair.getTag() != 'spring:beans' 
                and pair.getTag() != '/spring:beans'):
                self._mUnitTagList.append(pair)

    # Add standard xml definition and MUnit dependencies.
    # Grabs any spring:bean dependencies, as well as Mule xmlns dependency attributes.
    def _generateMUnitDependencies(self) -> None:
        # Set mule tag and attributes
        muleAttributes = OrderedDict()
        muleAttributes['closeAtEnd'] = False
        muleAttributes['xmlns'] = 'http://www.mulesoft.org/schema/mule/core'
        muleAttributes['xmlns:mock'] = 'http://www.mulesoft.org/schema/mule/mock'
        muleAttributes['xmlns:munit'] = 'http://www.mulesoft.org/schema/mule/munit'
        muleAttributes['xmlns:doc'] = 'http://www.mulesoft.org/schema/mule/documentation'
        muleAttributes['xmlns:spring'] = 'http://www.springframework.org/schema/beans'
        muleAttributes['xmlns:core'] = 'http://www.mulesoft.org/schema/mule/core'
        muleAttributes['version'] = 'EE-3.7.3'
        muleAttributes['xmlns:xsi'] = 'http://www.w3.org/2001/XMLSchema-instance'
        muleAttributes['xsi:schemaLocation'] = """http://www.mulesoft.org/schema/mule/mock http://www.mulesoft.org/schema/mule/mock/current/mule-mock.xsd
http://www.mulesoft.org/schema/mule/munit http://www.mulesoft.org/schema/mule/munit/current/mule-munit.xsd
http://www.springframework.org/schema/beans http://www.springframework.org/schema/beans/spring-beans-current.xsd
http://www.mulesoft.org/schema/mule/core http://www.mulesoft.org/schema/mule/core/current/mule.xsd"""
        self._mUnitTagList.append(TagPair('mule', muleAttributes))
        # Set munit:config tag and attributes
        configAttributes = OrderedDict()
        configAttributes['closeAtEnd'] = True
        configAttributes['name'] = "munit"
        configAttributes['doc:name'] = 'Munit configuration'
        self._mUnitTagList.append(TagPair('munit:config', configAttributes))
        # Set spring tags and attributes
        springBeansAttributes = OrderedDict()
        springBeansAttributes['closeAtEnd'] = False
        self._mUnitTagList.append(TagPair('spring:beans', springBeansAttributes))
        # Add a spring import for the file we're testing, and copy any spring internal values from the file
        springInternalAttributes = OrderedDict()
        springInternalAttributes['closeAtEnd'] = True
        springInternalAttributes['resource'] = 'classpath:' + self._inputFileName
        self._mUnitTagList.append(TagPair('spring:import', springInternalAttributes))
        self._extractSpringInternals()  # Extract spring tags and insert them into the MUnit TagList
        self._mUnitTagList.append(TagPair('/spring:beans', springBeansAttributes))
        
    # Generates MUnit Test Flows given the operations performed in a choice block, 
    # and a TagList of a flow containing a choicePlaceholder tag.
    # Can raise a type error if invalid parameter types are provided.
    def _generateMUnitTestFlows(self, choiceOperations : TagList, mUnitBaseTagList : TagList) -> []:
        if not isinstance(choiceOperations, TagList) or not isinstance(mUnitBaseTagList, TagList):
            raise TypeError('Invalid parameter types passed to MuleLines _generateMUnitTestFlows')
        outputFlows = []
        # Create a flow for each choice operation. (Later support should include multiple operations)
        for choiceOp in choiceOperations.pairs():
            for pair in mUnitBaseTagList.pairs():
                if pair.getTag() == 'choicePlaceholder':
                    # replace placeholder with choiceOperation
                    pair.setTag(choiceOp.getTag())
                    pair.setAttributes(choiceOp.getAttributes())
            outputFlows.append(mUnitBaseTagList)     
        return outputFlows
        
    # Iterates through the muleTagList and returns a list of TagLists, where each
    # returned TagList is a mule flow.
    def _isolateFlows(self) -> []:
        flows = []
        inFlow = False
        flowList = TagList()
        for pair in self._muleTagList.pairs():
            # If within a flow or sub-flow block, add the pair to the outputList
            if pair.getTag() == 'flow' or pair.getTag() == 'sub-flow':
                inFlow = True
                flowList.append(pair)
            elif pair.getTag() == '/flow' or pair.getTag() == '/sub-flow':
                flowList.append(pair)
                flows.append(flowList.copy())
                flowList.clear()  # Clear the flowList to handle next flow
                inFlow = False
            elif inFlow:
                flowList.append(pair)
        return flows
    
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
