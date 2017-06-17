import shlex
from collections import OrderedDict

class PairList:
    def __init__(self):
        self._list = []
        
    def keys(self):
        return [x[0] for x in self._list]
        
    def insert(self, pair):
        self._list.append(pair)
        
    def remove(self, key):
        for pair in self._list:
            if pair[0] == key:
                self._list.remove(pair)
                return
            
    def get(self, tag):
        for pair in self._list:
            if pair[0] == tag:
                return pair[1]
        return None        
    
    def toString(self):
        return str(self._list)    
        
class MuleLines:
    def __init__(self):
        self._tagList = PairList()
        
    def createMuleDict(self, lines):
        for line in lines:
            if line[0] == '<' and not line[1] == '?':
                splitLine = shlex.split(line) # Preserves spaces inside quoted strings
                attrDict = OrderedDict()
                if len(splitLine) > 1:
                    for item in splitLine[1:]:
                        attrAndValue = item.split('=')
                        attrDict[attrAndValue[0]] = attrAndValue[1].strip('/>')
                    self._tagList.insert((splitLine[0].lower(), attrDict))
                else:
                    self._tagList.insert((splitLine[0], None))
        
    def createMUnitDict(self):
        # Vars to monitor position during parsing
        inFlow = False
        inChoice = False
        testCount = 0
        mUnitTagList = PairList()
        
        for tag in self._tagList.keys():
            muleAttributes = self._tagList.get(tag)
            mUnitAttributes = dict()
            
            if tag == '<flow':
                testCount = testCount + 1
                inFlow = True
                for key in muleAttributes.keys():
                    if key == 'name':
                        mUnitAttributes['name'] = 'doc-test-' + muleAttributes.get(key) + 'Test' + str(testCount)
                mUnitTagList.insert(('<munit:test', mUnitAttributes))
                
            elif tag == '<sub-flow':
                testCount = testCount + 1
                inFlow = True
                for key in muleAttributes.keys():
                    if key == 'name':
                        mUnitAttributes['name'] = 'doc-test-' + muleAttributes.get(key) + 'Test' + str(testCount)
                mUnitTagList.insert(('<munit:test', mUnitAttributes))
                
            elif tag == '<http:listener':
                continue
                
            elif tag == '<set-payload':
                mUnitAttributes['payload'] = ''
                for key in muleAttributes.keys():
                    if key == 'doc:name':
                        mUnitAttributes['doc:name'] = 'Set Message Payload for Test ' + str(testCount)
                mUnitTagList.insert(('<munit:set', mUnitAttributes))
                
            elif tag == '<flow-ref':
                for key in muleAttributes.keys():
                    if key == 'name':
                        mUnitAttributes['name'] = muleAttributes.get('name')
                    elif key == 'doc:name':
                        mUnitAttributes['doc:name'] = muleAttributes.get('doc:name')
                mUnitTagList.insert(('<munit:set', mUnitAttributes))
                
            elif tag == '<choice':
                inChoice = True
                        
            elif tag == '<when':
                continue
                #testCount = testCount + 1
                
            elif tag == '<otherwise':
                continue
                #testCount = testCount + 1
                
            elif tag == '<set-variable':
                a=1
                
            elif tag == '</flow>':
                testCount = 0
                inFlow = False
                mUnitTagList.insert(('</munit:test>', None))
                
            elif tag == '</sub-flow>':
                testCount = 0
                inFlow = False
                mUnitTagList.insert(('</munit:test>', None))
                
            elif tag == '</when>':
                continue
            elif tag == '</otherwise>':
                continue
            elif tag == '</choice>':
                inChoice = False
            elif tag == '</mule>':
                mUnitTagList.insert(('</mule>', None))
            
            self._tagList.remove(tag)
            
        return mUnitTagList
    
    def _createMUnitAttributes(self, attribsDict):
        for key in attribsDict.keys():
            print key, attribsDict.get(key)
        
    