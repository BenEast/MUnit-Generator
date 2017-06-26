# MUnit-Generator
This project is my attempt at creating a script that can parse a Mule XML file and procedurally generate an MUnit Test Suite XML file. It is still a work in progress, however it can generate a decent base test structure for basic Mule flows.

## How It Works
The "magic" of this project takes place in the MuleLines file, where all file parsing, mapping, and conversion are handled. 

First, the input file is read in and mapped to a list of pairs, where each pair is an XML tag mapped to an OrderedDict of it's attributes. To simplify use of this data structure, I created TagList and TagPair as meta-classes with easy-to-use methods. Once the file has been read in, it is mapped to a TagList.

Next, each Mule flow is parsed separately. During this process, any operations performed in choice blocks are extracted, and all choice blocks are replaced with a choicePlaceholder tag. Multiple tests are generated for each choice case (that is, "when" or "otherwise" cases in Mule code). This allows for coverage of each choice case, and provides an individual test for each. 

Each of the resulting flows are then converted from Mule XML to MUnit XML, and stored within the MuleLines object. The test flows can be written to the specified output file by calling MuleLines.createMUnitSuiteFile. When the file is created, indentation is handled dynamically, by tracking which of the preceding tags were self closing, and which were left open.  This results in a correctly indented XML file structure.
