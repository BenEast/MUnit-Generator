import argparse
from MuleLines import *

# REFACTORING:
# Complete MuleLines implementation
# Migrate dependency tag generation to MuleLines
# Add support for all components
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
        
def main():
    print ('Please input your desired file to test and output directory.\n'
            'Use /input and /output to specify your file and directory.\n\n')
    parser = argparse.ArgumentParser()
    parser.add_argument('/input', type=str, required=True, help='Input file path')
    parser.add_argument('/output', type=str, required=True, help='Output file path')
    
    args = parser.parse_args()
    
    if args.input and args.output:
        outputFile = args.output
        mule = MuleLines()
        muleFileLines = getMuleFileLines(args.input)
        mule.createMuleDict(muleFileLines)
        mUnitBody = mule.createMUnitDict()
        
        #generateBaseMUnitFile(outputFile)
        #generateDependencyTags(outputFile, muleFileLines)
    else:
        print 'Invalid input! Must specify both /input and /output directories.'
    
def testMain():
        outputFile = 'munitTest.xml'
        mule = MuleLines()
        muleFileLines = getMuleFileLines('example.xml')
        mule.createMuleDict(muleFileLines)
        mUnitBody = mule.createMUnitDict()
        for key in mUnitBody.keys():
            print key, '\t', mUnitBody.get(key)
            
        #generateBaseMUnitFile(outputFile)
        #generateDependencyTags(outputFile, muleFileLines)
    
if __name__ == "__main__":
    testMain()
