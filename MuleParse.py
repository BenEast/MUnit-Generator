import sys
from MuleLines import MuleLines

###########################
# Author: Benjamin East
# Last Updated: 06/23/2017
###########################

# Reads the specified file and returns a list of file lines.
# Splits whitespace and takes only lines beginning in tags (doesn't directly parse Mule dependencies)
def getMuleFileLines(filename : str) -> []:
    try:
        muleFileLines = open(filename, 'r').readlines()
    except IOError as error:
        print(error.error())
        print('Please input a valid output file path.')
        return
    except:
        print('Unexpected error:', sys.exc_info()[0])
        return
    
    muleFileLines = list(filter(None, [x.lstrip(' ').strip() for x in muleFileLines]))
    for line in muleFileLines:
        if not line[0] == "<":
            muleFileLines.remove(line)
    return muleFileLines
    
# Writes MUnit dependencies and base XML to a file. 
# This will eventually be removed and replaced with functionality in MuleLines
def generateBaseMUnitFile(filename):
    with open(filename, 'w+') as output:
        output.write("""<?xml version="1.0" encoding="UTF-8"?>

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

# Generates file dependency tags based on the given mule XML file lines.
# This will eventually be removed and replaced with functionality in MuleLines
def generateDependencyTags(outputFile, muleFileLines):
    with open(outputFile, 'a') as output:
        for line in muleFileLines:
            if line[:12] == '<spring:bean ' or line[:12] == '<spring:prop' or line[:12] == '</spring:bean':
                output.write('\t\t' + line)
        output.write('\t</spring:beans>\n\n')

# Main method for development/testing purposes
def devMain():
        outputFile = 'munitTest.xml'
        mule = MuleLines()
        muleFileLines = getMuleFileLines('example.xml')
        mule.parseMuleFileLines(muleFileLines)
        mule.createMUnitTests()
        
        generateBaseMUnitFile(outputFile)
        generateDependencyTags(outputFile, muleFileLines)
        mule.createMUnitSuiteFile(outputFile)
    
if __name__ == "__main__":
    devMain()
