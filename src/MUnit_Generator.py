import argparse
import time
from MuleLines import MuleLines

###########################
# Author: Benjamin East
# Last Updated: 06/25/2017
###########################

# Main method for development/testing purposes
def main() -> None:

    print('Please provide the input file path and output file path using the --input and --output commands.\n')
    print('Please format the file paths as follows: C:/folder/filename or just filename\n\n')
    parser = argparse.ArgumentParser()
    parser.add_argument('--input', type = str, required = True, help = 'Input file name')
    parser.add_argument('--output', type = str, required = True, help = 'Output file name')
    args = parser.parse_args()
    inputFile = args.input
    outputFile = args.output

    print('Generating MUnit Test File...')
    startTime = time.time()
        
    mule = MuleLines()
    mule.parseMuleFileLines(inputFile)
    mule.createMUnitTests()
    mule.createMUnitSuiteFile(outputFile)
    
    print('Finished.')
    print('Total execution time: ', str(time.time() - startTime))

if __name__ == "__main__":
    main()