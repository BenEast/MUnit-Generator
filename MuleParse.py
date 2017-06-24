import argparse
import time
from MuleLines import MuleLines

###########################
# Author: Benjamin East
# Last Updated: 06/24/2017
###########################

# Main method for development/testing purposes
def main():
        startTime = time.time()
        
        inputFile = 'example.xml'
        outputFile = 'munitTest.xml'
        
        mule = MuleLines()
        mule.parseMuleFileLines(inputFile)
        mule.createMUnitTests()
        mule.createMUnitSuiteFile(outputFile)

        print('Total execution time: ', str(time.time() - startTime))
        
if __name__ == "__main__":
    main()
