import os
import shlex
import sys
from collections import OrderedDict
from TagList import TagList
from TagPair import TagPair

###########################
# Author: Benjamin East
# Last Updated: 07/01/2017
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
        # isolateFlows returns an array of TagLists, which are each a mule flow
        for flow in self._isolateFlows():
            # Convert operations in choice blocks to mUnit code
            mUnitChoiceOperations = self._extractChoiceOperations(flow)
            self._replaceChoiceBlocks(flow)
            
            # Generate multiple test flows if a choice block is present
            if flow.containsTag('choicePlaceholder'):
                for flow in self._generateMUnitTestFlows(mUnitChoiceOperations, flow):
                    mUnitFlow = self._convertMuletoMUnit(flow)  # Convert each test flow to MUnit
                    for pair in mUnitFlow.pairs():
                        self._mUnitTagList.append(pair)
                        
            else:  # Otherwise, create a single test flow
                mUnitFlow = self._convertMuletoMUnit(flow)
                for pair in mUnitFlow.pairs():
                    self._mUnitTagList.append(pair)

        self._mUnitTagList.append(TagPair('/mule', OrderedDict({'closeAtEnd': False})))

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
                        currentFlow = pair.getAttribute('name')
                        testNumber = 1
                        
                    else:
                        testNumber += 1
                        
                # Create the MUnit file lines and write them to the output file.
                mUnitLine = '<' + pair.getTag()
                attributes = pair.getAttributes()
                for attribute in pair.getAttributes():
                    if pair.getTag() == 'munit:test' and attribute == 'name':
                        mUnitLine = (mUnitLine + ' ' + attribute + '="' + attributes.get(attribute) 
                                        + str(testNumber) + '"')
                        
                    elif attribute != 'closeAtEnd':
                        mUnitLine = mUnitLine + ' ' + attribute + '="' + attributes.get(attribute) + '"'
               
                # Add closing braces depending on the tag type
                if pair.getAttribute('closeAtEnd'):
                        mUnitLine += '/>\n'
                        
                else:
                    mUnitLine += '>\n'
                    
                # Insert an additional newline for readability
                if (pair.getTag() == '/munit:test' or pair.getTag() == '/spring:beans' or 
                    pair.getTag() == '/munit:before-suite' or pair.getTag() == '/munit:after-suite'):
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
    def parseMuleFileLines(self, inputFilePath : str) -> None:
        self._extractMuleFileLines(inputFilePath)
        self._inputFileName = os.path.basename(inputFilePath)  # Take only the filename
        
        for line in self._muleFileLines:
            if line[0] == '<' and line[1] != '?' and line[1] != '!':
                splitLine = shlex.split(line)  # Split the line; preserves spaces in quoted strings.
                attrDict = OrderedDict()
                
                if len(splitLine) > 1:  # Map additional attributes to attrDict
                    for item in splitLine[1:]:  # Skip the tag in the line
                        attrAndValue = item.split('=')
                        
                        # Add a closeAtEnd attribute, for use in writing the final output file
                        if attrAndValue[1][-2:] == '/>':
                            attrDict['closeAtEnd'] = True
                            attrDict[attrAndValue[0]] = attrAndValue[1][:-2]  # Strip closing bracket
                            
                        elif attrAndValue[1][-1:] == '>':
                            attrDict['closeAtEnd'] = False
                            attrDict[attrAndValue[0]] = attrAndValue[1][:-1]  # Strip closing bracket
                        
                        else:  # Add to the dict if it's a middle attribute
                            attrDict[attrAndValue[0]] = attrAndValue[1]
                    
                    self._muleTagList.append(TagPair(splitLine[0].lower().strip('<'), attrDict))
                    
                else:  # Add a closeAtEnd attribute, for use in writing the final output file
                    if splitLine[0][:2] == '</':
                        attrDict['closeAtEnd'] = False
                    
                    else:
                        attrDict['closeAtEnd'] = True
                    
                    self._muleTagList.append(TagPair(splitLine[0].lower().strip('<').strip('>'), attrDict))
    
    # Convert a mule flow to a TagList of MUnit code.
    # Can raise a TypeError if incorrect parameter types are provided.
    def _convertMuletoMUnit(self, muleFlowTagList : TagList) -> TagList:
        if not isinstance(muleFlowTagList, TagList):
            raise TypeError('Invalid parameter passed to MuleLines _convertMuletoMUnit')
        self._replaceChoiceBlocks(muleFlowTagList)  # Replace choice blocks with choicePlaceholder
        
        # Values used for tracking info throughout the method
        muleFlowName = ""
        mUnitTagList = TagList()
        afterChoiceBlock = True  # Used to determine certain tag types
        flowContainsDatabase = False  # Used to create before and after flows for DB mocking
        flowContainsFTP = False
        
        # Define generic OrderedDicts for commonly used tag attributes
        noAttributes = OrderedDict({'closeAtEnd': False})
        mockReturn = OrderedDict({'closeAtEnd': False, 'payload': '#[]'})
        mockAttribute = OrderedDict({'closeAtEnd': True, 'name': 'name'})
        mockWhen = OrderedDict({'closeAtEnd': False, 'doc:name': 'Mock'})
                
        # Iterate through the Mule XML tags and attributes to create MUnit tags and attributes.
        if muleFlowTagList.containsTag('choicePlaceholder'):
            afterChoiceBlock = False

        # Check if a DB connector is in the flow
        if (muleFlowTagList.containsTag('db:select') or muleFlowTagList.containsTag('db:insert') or
             muleFlowTagList.containsTag('db:update') or muleFlowTagList.containsTag('db:delete') or 
             muleFlowTagList.containsTag('db:stored-procedure') or muleFlowTagList.containsTag('db:bulk-execute')
             or muleFlowTagList.containsTag('db:execute-ddl')):
            
            flowContainsDatabase = True
            
            # Create before suite block to start a DB mock
            beforeAttributes = OrderedDict({'closeAtEnd': False, 'name': 'before-DB',
                                            'description': 'Start DB Server'})
            mUnitTagList.append(TagPair('munit:before-suite', beforeAttributes))
            
            startAttributes = OrderedDict({'closeAtEnd': True, 'config-ref': '', 'doc:name': 'Start DB'})
            mUnitTagList.append(TagPair('dbserver:start-db-server', startAttributes))
            mUnitTagList.append(TagPair('/munit:before-suite', noAttributes))
            
        # Check if FTP connector is in the flow
        if muleFlowTagList.containsTag('ftp:outbound-endpoint'):
            flowContainsFTP = True
            
            # Add FTP before-suite block to start an FTP mock
            beforeAttributes = OrderedDict({'closeAtEnd': False, 'name': 'before-FTP',
                                            'description': 'Start DB Server'})
            mUnitTagList.append(TagPair('munit:before-suite', beforeAttributes))
            startAttributes = OrderedDict({'closeAtEnd': True, 'config-ref': '', 'doc:name': 'Start FTP'})
            mUnitTagList.append(TagPair('dbserver:start-db-server', startAttributes))
            mUnitTagList.append(TagPair('/munit:before-suite', noAttributes))
            
        # Iterate the TagPairs in the mule flow
        flowPairs = muleFlowTagList.pairs()
        for pair in flowPairs:
            muleAttributes = pair.getAttributes()  # Attributes for the given Mule XML tag
            
            # Handle choicePlaceholder tag       
            if pair.getTag() == 'choicePlaceholder':
                afterChoiceBlock = True
                muleFlowTagList.remove(pair)
                
                # Insert flow ref to Mule flow
                flowRef = OrderedDict({'closeAtEnd': True, 'name': muleFlowName, 'doc:name': 
                                       'Flow-ref to ' + muleFlowName})
                mUnitTagList.append(TagPair('flow-ref', flowRef))
            
            # Handle flow tag
            elif pair.getTag() == 'flow':
                flowAttributes = OrderedDict({'closeAtEnd': False})
                
                if 'name' in muleAttributes:  # Get the name, store it and set MUnit test name
                    muleFlowName = muleAttributes.get('name')
                    flowAttributes['name'] = muleAttributes.get('name') + '-test-'
                    flowAttributes['description'] = 'Unit Test for ' + muleAttributes.get('name')
                
                else:  # Set generic MUnit test name
                    flowAttributes['name'] = 'UnitTestFlow'
                    flowAttributes['description'] = 'Unit Test Flow for unnamed Mule Flow'
                    
                mUnitTagList.append(TagPair('munit:test', flowAttributes)) 
                
                # Place a mock payload if a payload isn't set at the start of the flow 
                nextPairTag = flowPairs[flowPairs.index(pair) + 1].getTag() 
                if (nextPairTag != 'set-payload' and nextPairTag != 'http:listener' 
                    and not 'inbound-endpoint' in nextPairTag):
                    
                    setAttributes = OrderedDict({'closeAtEnd': True, 'payload': '',
                                                 'doc:name': 'Set Initial Test Payload'})
                    mUnitTagList.append(TagPair('munit:set', setAttributes))
                        
            # Handle flow-ref tag       
            elif pair.getTag() == 'flow-ref':  # Create MUnit structure for flow ref
                # Mock flow-ref to sub-flow
                if ('subflow' in muleAttributes['name'].lower() or 'sub-flow' in muleAttributes['name'].lower()
                    or 'sub_flow' in muleAttributes['name'].lower() or 'sub flow' in muleAttributes['name'].lower()):
                   
                    mockVerify = OrderedDict({'closeAtEnd': False, 'messageProcessor': 'mule:sub-flow',
                                              'doc:name': 'Verify Call', 'times': '1'})
                    mUnitTagList.append(TagPair('mock:verify-call', mockVerify))
                    mUnitTagList.append(TagPair('mock:with-attributes', noAttributes))
                    
                    mockAttributeCopy = mockAttribute.copy()
                    mockAttributeCopy['whereValue'] = "#[matchContains('" + muleAttributes['name'] + "')]"
                    mUnitTagList.append(TagPair('mock:with-attribute', mockAttributeCopy))
                    
                    mUnitTagList.append(TagPair('/mock:with-attributes', noAttributes))
                    mUnitTagList.append(TagPair('/mock:verify-call', noAttributes))
                    
                else:  # Mock flow-ref to flow
                    mockWhenCopy = mockWhen.copy()
                    mockWhenCopy['messageProcessor'] = 'mule:flow'
                    mUnitTagList.append(TagPair('mock:when', mockWhenCopy))
                    mUnitTagList.append(TagPair('mock:with-attributes', noAttributes))
                
                    mockAttributeCopy = mockAttribute.copy()
                    mockAttributeCopy['whereValue'] = "#['" + muleAttributes['name'] + "']"
                    mUnitTagList.append(TagPair('mock:with-attribute', mockAttributeCopy))
                    mUnitTagList.append(TagPair('/mock:with-attributes', noAttributes))
                    
                    mUnitTagList.append(TagPair('mock:then-return', mockReturn))
                    mUnitTagList.append(TagPair('mock:invocation-properties', noAttributes))
                    
                    # Leave key and value blank, until it's clear how to accurately populate them
                    mockProperty = OrderedDict({'closeAtEnd': True, 'key': '', 'value': ''})
                    mUnitTagList.append(TagPair('mock:invocation-property', mockProperty))
                    
                    mUnitTagList.append(TagPair('/mock:invocation-properties', noAttributes))
                    mUnitTagList.append(TagPair('/mock:then-return', noAttributes))
                    mUnitTagList.append(TagPair('/mock:when', noAttributes))
            
            # Handle ftp:outbound-endpoint tag
            elif pair.getTag() == 'ftp:outbound-endpoint':
                ftpAttributes = OrderedDict({'closeAtEnd': True, 'file': pair.getAttribute('outputPattern'),
                                             'path': pair.getAttribute('path'), 'config-ref': ''})
                mUnitTagList.append(TagPair('ftpserver:contains-files', ftpAttributes))
                        
            # If at the entrance point to the flow, set a payload if one isn't set after
            elif 'inbound-endpoint' in pair.getTag() or pair.getTag() == 'http:listener':
                if not flowPairs[flowPairs.index(pair) + 1].getTag() == 'set-payload':
                    
                    setAttributes = OrderedDict({'closeAtEnd': True, 'payload': '',
                                                 'doc:name': 'Set Initial Test Payload'})
                    mUnitTagList.append(TagPair('munit:set', setAttributes))

            # Handle set-payload tag
            elif pair.getTag() == 'set-payload':
                if afterChoiceBlock:  # Assert payload value
                    
                    assertPayload = OrderedDict({'closeAtEnd': True, 'message': 'Incorrect payload!',
                                                 'expectedValue': muleAttributes['value']})
                    mUnitTagList.append(TagPair('munit:assert-payload-equals', assertPayload))
                    
                else:  # if before choice block, mock payload value
                    mockWhenCopy = mockWhen.copy()
                    mockWhenCopy['messageProcessor'] = 'mule:set-payload'
                    mUnitTagList.append(TagPair('mock:when', mockWhenCopy))
                    mUnitTagList.append(TagPair('mock:with-attributes', noAttributes))
                    
                    mockAttributeCopy = mockAttribute.copy()
                    mockAttributeCopy['whereValue'] = "#['Set Original Payload']"
                    mockAttributeCopy['name'] = 'doc:name'
                    mUnitTagList.append(TagPair('mock:with-attribute', mockAttributeCopy))
                    mUnitTagList.append(TagPair('/mock:with-attributes', noAttributes))

                    mockReturnCopy = mockReturn.copy()
                    mockReturnCopy['closeAtEnd'] = True
                    mUnitTagList.append(TagPair('mock:then-return', mockReturnCopy))
                    mUnitTagList.append(TagPair('/mock:when', noAttributes))
 
            # Handle /flow tag 
            elif pair.getTag() == '/flow':
                mUnitTagList.append(TagPair('/munit:test', noAttributes))    
                
                # Add DB after-suite case
                if flowContainsDatabase:  # Create mUnit after-suite code to stop the database
                    
                    afterAttributes = OrderedDict({'closeAtEnd': False, 'name': muleFlowName + '-After_Suite_DB',
                                                   'description': 'Stop DB Server'})
                    mUnitTagList.append(TagPair('munit:after-suite', afterAttributes))
                    
                    stopAttributes = OrderedDict({'closeAtEnd': True, 'config-ref': '',
                                                  'doc:name': 'Stop Server'})
                    mUnitTagList.append(TagPair('dbserver:stop-db-server', stopAttributes))
                    mUnitTagList.append(TagPair('/munit:after-suite', noAttributes))
                
                # Add FTP after-suite case
                if flowContainsFTP:
                    
                    afterAttributes = OrderedDict({'closeAtEnd': False, 'name': muleFlowName + '-After_Suite_FTP',
                                                   'description': 'Stop FTP Server'})
                    mUnitTagList.append(TagPair('munit:after-suite', afterAttributes))
                    
                    stopAttributes = OrderedDict({'closeAtEnd': True, 'config-ref': ''})
                    mUnitTagList.append(TagPair('ftpserver:stop-server', stopAttributes))
                    mUnitTagList.append(TagPair('/munit:after-suite', noAttributes))
            
            # Handle /mule tag
            elif pair.getTag() == '/mule':
                mUnitTagList.append(TagPair('/mule', noAttributes))
                
        return mUnitTagList
    
    # Extracts operations performed in a choice block in the provided flow.
    # Returns a TagList containing the choice operations.
    # Can raise a TypeError if an incorrect parameter type is provided.
    def _extractChoiceOperations(self, flowTagList : TagList) -> []:
        if not isinstance(flowTagList, TagList):
            raise TypeError('Invalid parameter type passed to MuleLines _extractChoiceOperations')
        
        choiceOperations = []
        caseOperations = TagList()
        inChoiceClause = False
        for pair in flowTagList.pairs():
            if pair.getTag() == 'when' or pair.getTag() == 'otherwise':
                inChoiceClause = True
                
            elif pair.getTag() == '/when' or pair.getTag() == '/otherwise':
                inChoiceClause = False
                choiceOperations.append(caseOperations.copy())
                caseOperations.clear()
                
            elif inChoiceClause:
                caseOperations.append(pair)
                
        return choiceOperations
    
    # Reads the specified file and returns a list of file lines.
    # Splits whitespace and takes only lines beginning in tags
    def _extractMuleFileLines(self, inputFilePath : str) -> None:
        with open(inputFilePath, 'r') as file:
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
        muleAttributes['\n\txmlns:mock'] = 'http://www.mulesoft.org/schema/mule/mock'
        muleAttributes['xmlns:munit'] = 'http://www.mulesoft.org/schema/mule/munit'
        muleAttributes['\n\txmlns:doc'] = 'http://www.mulesoft.org/schema/mule/documentation'
        muleAttributes['xmlns:spring'] = 'http://www.springframework.org/schema/beans'
        muleAttributes['\n\txmlns:core'] = 'http://www.mulesoft.org/schema/mule/core'
        muleAttributes['version'] = 'EE-3.7.3'
        muleAttributes['\n\txmlns:xsi'] = 'http://www.w3.org/2001/XMLSchema-instance'
        muleAttributes['\n\txsi:schemaLocation'] = """http://www.mulesoft.org/schema/mule/mock 
    http://www.mulesoft.org/schema/mule/mock/current/mule-mock.xsd http://www.mulesoft.org/schema/mule/munit 
    http://www.mulesoft.org/schema/mule/munit/current/mule-munit.xsd http://www.springframework.org/schema/beans 
    http://www.springframework.org/schema/beans/spring-beans-current.xsd http://www.mulesoft.org/schema/mule/core 
    http://www.mulesoft.org/schema/mule/core/current/mule.xsd"""
        self._mUnitTagList.append(TagPair('mule', muleAttributes))
        
        # Set munit:config tag and attributes
        configAttributes = OrderedDict({'closeAtEnd': True, 'name': 'munit', 'doc:name': 'Munit Configuration'})
        self._mUnitTagList.append(TagPair('munit:config', configAttributes))
        
        # Set spring tags and attributes
        self._mUnitTagList.append(TagPair('spring:beans', OrderedDict({'closeAtEnd': False})))
        
        # Add a spring import for the file we're testing, and copy any spring internal values from the file
        springInternalAttributes = OrderedDict({'closeAtEnd': True, 'resource': 
                                                'classpath:' + self._inputFileName})
        self._mUnitTagList.append(TagPair('spring:import', springInternalAttributes))
        
        self._extractSpringInternals()  # Extract spring tags and insert them into the MUnit TagList
        self._mUnitTagList.append(TagPair('/spring:beans', OrderedDict({'closeAtEnd': False})))
        
    # Generates MUnit Test Flows given the operations performed in a choice block 
    # and a TagList of a flow containing a choicePlaceholder tag.
    # Can raise a type error if invalid parameter types are provided.
    def _generateMUnitTestFlows(self, choiceOperations : [], mUnitBaseTagList : TagList) -> []:
        if not isinstance(choiceOperations, list) or not isinstance(mUnitBaseTagList, TagList):
            raise TypeError('Invalid parameter types passed to MuleLines _generateMUnitTestFlows')
        outputFlows = []
        
        # Create a flow for each choice operation. (Later support should include multiple operations)
        for choiceTagList in choiceOperations:
            mUnitCopy = mUnitBaseTagList.copy()
            pair = mUnitCopy.getPair('choicePlaceholder')
            pairIndex = mUnitCopy.index(pair)
            
            for choicePair in choiceTagList.pairs():
                pairIndex += 1  # Increment index for each pair to maintain correct order
                mUnitCopy.insertAtIndex(pairIndex, choicePair)
            outputFlows.append(mUnitCopy)    
             
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
