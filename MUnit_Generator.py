import argparse
import time
from MuleLines import MuleLines

###########################
# Author: Benjamin East
# Last Updated: 06/24/2017
###########################

# Main method for development/testing purposes
def main():
    """   
    parser = argparse.ArgumentParser()
    parser.add_argument('--input', type = str, required = True, help = 'Input file name')
    parser.add_argument('--output', type = str, required = True, help = 'Output file name')
    args = parser.parse_args()
    inputFile = args.input
    outputFile = args.output
    """
    inputFile = 'example.xml'
    outputFile = 'munitTest.xml'
        
    startTime = time.time()
        
    mule = MuleLines()
    mule.parseMuleFileLines(inputFile)
    mule.createMUnitTests()
    mule.createMUnitSuiteFile(outputFile)
    
    print('Total execution time: ', str(time.time() - startTime))

if __name__ == "__main__":
    main()