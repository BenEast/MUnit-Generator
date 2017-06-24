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
    # Initialize a list for original mule XML code, and two 
    # TagList objects for existing Mule code and MUnit code to be generated.
    def __init__(self):
        self._inputFileName = ""
        self._muleFileLines = []
        self._muleTagList = TagList()
        self._mUnitTagList = TagList()
        
    # Reads the specified file and returns a list of file lines.
    # Splits whitespace and takes only lines beginning in tags
    def _extractMuleFileLines(self, inputFileName : str) -> None:
        try:
            self._muleFileLines = open(inputFileName, 'r').readlines()
        except IOError as error:
            print(error.error())
            print('Please input a valid output file path.')
            return
        except:
            print('Unexpected error:', sys.exc_info()[0])
            return
        self._muleFileLines = list(filter(None, [x.lstrip(' ').strip() for x in self._muleFileLines]))
        for line in self._muleFileLines:
            if not line[0] == "<":
                self._muleFileLines.remove(line)

    # Parse XML lines of Mule code into the _muleTagList for this object.
    def parseMuleFileLines(self, inputFileName) -> None:
        self._inputFileName = inputFileName
        self._extractMuleFileLines(inputFileName)
        for line in self._muleFileLines:
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
                        # Add a closeAtEnd attribute, for use in writing the final output file
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
                    # Add a closeAtEnd attribute, for use in writing the final output file
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
        flowList = TagList()
        for pair in self._muleTagList.pairs():
            # If within a flow or sub-flow block, add the pair to the outputList
            if pair.getTag() == 'flow' or pair.getTag() == 'sub-flow':
                inFlow = True
                flowList.append(pair)
            elif pair.getTag() == '/flow' or pair.getTag() == '/sub-flow':
                flowList.append(pair)
                flows.append(flowList.copy())
                # Clear the outputList in case another flow is present later
                flowList.clear()
                inFlow = False
            elif inFlow:
                flowList.append(pair)
        return flows
    
    # Generates MUnit Test Flows given the operations performed in a choice block, 
    # and a TagList of a flow containing a choicePlaceholder tag.
    # Can raise a type error if invalid parameter types are provided.
    def _generateMUnitTestFlows(self, choiceOperations : TagList,
                                      mUnitBaseTagList : TagList) -> []:
        if not isinstance(choiceOperations, TagList) or not isinstance(mUnitBaseTagList, TagList):
            raise TypeError('Invalid parameter types passed to MuleLines _generateMUnitTestFlows')
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
                        pair.setAttribute('name', pair.getAttributes().get('name') + '-' + str(testCount))
                    else:
                        pair.setAttribute('name', 'MUnitTestFlow-' + str(testCount))
            # Add test count number as applicable        
            testCount += 1
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
            
            if pair.getTag() == 'flow':
                if 'name' in muleAttributes:
                    mUnitAttributes['name'] = str(muleAttributes.get('name')) + '_test'
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
    
    # Add standard xml definition and MUnit dependencies.
    # Grabs any spring:bean dependencies, as well as Mule xmlns dependency attributes.
    def _generateMUnitDependencies(self):
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
        springImportAttributes = OrderedDict()
        springImportAttributes['closeAtEnd'] = True
        springImportAttributes['resource'] = 'classpath:' + self._inputFileName
        self._mUnitTagList.append(TagPair('spring:import', springImportAttributes))
        self._mUnitTagList.append(TagPair('/spring:beans', springBeansAttributes))
        
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
            # Iterate through the TagPairs, create MUnit lines, and write them to the file.
            for pair in self._mUnitTagList.pairs():                
                # Create the MUnit file lines and write them to the output file.
                mUnitLine = '<' + pair.getTag()
                attributes = pair.getAttributes()
                for attribute in attributes:
                    if not attribute == 'closeAtEnd':
                        mUnitLine = mUnitLine + ' ' + attribute + '="' + attributes.get(attribute) + '"'
                if pair.getAttribute('closeAtEnd'):
                        mUnitLine += '/>\n'
                else:
                    mUnitLine += '>\n'
                if pair.getTag() == '/munit:test':
                    mUnitLine += '\n'
                
                if not pair.getTag()[0] == '/':
                    file.write('\t' * tagDepth + mUnitLine)
                # Determine the indentation of current XML tag based on when blocks close
                if pair.getTag()[0] == '/':
                    file.write('\t' * (tagDepth - 1) + mUnitLine)
                    tagDepth -= 1
                elif not pair.getAttribute('closeAtEnd'):
                    tagDepth += 1
            file.close()
