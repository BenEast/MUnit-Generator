import argparse
from MuleLines import *

# REFACTORING:
# ISSUE: contents of when/otherwise not parsed correctly (or at all) --> getMuleFileLines
# Add support for all components
# Add argparse inputs
# Document code

def getMuleFileLines(filename):
    muleFileLines = open(filename, 'r').readlines()
    muleFileLines = filter(None, [x.lstrip(' ').strip() for x in muleFileLines])
    
    for line in muleFileLines:
        if not line[0] == "<":
            muleFileLines.remove(line)
            
    return muleFileLines
    
def generateBaseMUnitFile(filename):
    with open(filename, 'w+') as output:
        output.write("""
<?xml version="1.0" encoding="UTF-8"?>

<mule xmlns="http://www.mulesoft.org/schema/mule/core" xmlns:mock="http://www.mulesoft.org/schema/mule/mock"
        xmlns:munit="http://www.mulesoft.org/schema/mule/munit" xmlns:doc="http://www.mulesoft.org/schema/mule/documentation"
        xmlns:spring="http://www.springframework.org/schema/beans" xmlns:core="http://www.mulesoft.org/schema/mule/core"
        version="EE-3.7.3" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
        xsi:schemaLocation="http://www.mulesoft.org/schema/mule/mock http://www.mulesoft.org/schema/mule/mock/current/mule-mock.xsd
http://www.mulesoft.org/schema/mule/munit http://www.mulesoft.org/schema/mule/munit/current/mule-munit.xsd
http://www.springframework.org/schema/beans http://www.springframework.org/schema/beans/spring-beans-current.xsd
http://www.mulesoft.org/schema/mule/core http://www.mulesoft.org/schema/mule/core/current/mule.xsd">

    <munit:config name="munit" doc:name="Munit configuration"/>
    <spring:beans>
""")

def generateDependencyTags(filename, muleFileLines):
    lastImportIndex = 0
    with open(filename, 'a') as output:
        for line in muleFileLines:
            if line[:12] == '<spring:bean ' or line[:12] == '<spring:prop' or line[:12] == '</spring:bean':
                output.write('\t\t' + line)
                lastImportIndex = muleFileLines.index(line)
        output.write('\t</spring:beans>')
    
    # Remove lines that have already been parsed
    del muleFileLines[:lastImportIndex]    
        
def generateMUnitBody(filename, muleFileLines):
    MUnitBody = [] # Create MUnit tags as we iterate through the lines
    for line in muleFileLines:
        MUnitBody.append('') 
        
    with open(filename, 'a') as output:
        for line in MUnitBody:
            output.write(line)
        output.write('</mule>')
        
def main():
    outputFile = 'munit.xml'
    muleFileLines = getMuleFileLines('example.xml')
    mule = MuleLines()
    mule.createMuleDict(muleFileLines)
    print str(mule.createMUnitDict())
    
    #generateBaseMUnitFile(outputFile)
    #generateDependencyTags(outputFile, muleFileLines)
    #generateMUnitBody(outputFile, muleFileLines)
    
if __name__ == "__main__":
    main()
