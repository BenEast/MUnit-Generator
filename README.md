# MUnit-Generator
This project is my attempt at creating a script that can parse a Mule XML file and procedurally generate an MUnit Test Suite XML file. It is still a work in progress, however it can generate a decent base test structure for basic Mule flows.

## How It Works
The "magic" of this project takes place in the MuleLines file, where all file parsing, mapping, and conversion are handled. 

First, the input file is read in and mapped to a list of pairs, where each pair is an XML tag mapped to an OrderedDict of it's attributes. To simplify use of this data structure, I created TagList and TagPair as meta-classes with easy-to-use methods. Once the file has been read in, it is mapped to a TagList.

Next, each Mule flow is parsed separately. During this process, any operations performed in choice blocks are extracted, and all choice blocks are replaced with a choicePlaceholder tag. Multiple tests are generated for each choice case (that is, "when" or "otherwise" cases in Mule code). This allows for coverage of each choice case, and provides an individual test for each. 

Each of the resulting flows are then converted from Mule XML to MUnit XML, and stored within the MuleLines object. The test flows can be written to the specified output file by calling MuleLines.createMUnitSuiteFile. When the file is created, indentation is handled dynamically, by tracking which of the preceding tags were self closing, and which were left open.  This results in a correctly indented XML file structure.

## Current Functionality
The current MUnit Generator version is capable of setting up the majority of the MUnit code necessary to test simple flows.

For example, given the following Mule example flow (taken from https://docs.mulesoft.com/munit/v/1.3/munit-short-tutorial):
```
<?xml version="1.0" encoding="UTF-8"?>

<mule xmlns:http="http://www.mulesoft.org/schema/mule/http"
        xmlns:tracking="http://www.mulesoft.org/schema/mule/ee/tracking" xmlns="http://www.mulesoft.org/schema/mule/core"
        xmlns:doc="http://www.mulesoft.org/schema/mule/documentation"
        xmlns:spring="http://www.springframework.org/schema/beans" version="EE-3.7.3"
        xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
        xsi:schemaLocation="http://www.springframework.org/schema/beans http://www.springframework.org/schema/beans/spring-beans-current.xsd
http://www.mulesoft.org/schema/mule/core http://www.mulesoft.org/schema/mule/core/current/mule.xsd
http://www.mulesoft.org/schema/mule/ee/tracking http://www.mulesoft.org/schema/mule/ee/tracking/current/mule-tracking-ee.xsd
http://www.mulesoft.org/schema/mule/http http://www.mulesoft.org/schema/mule/http/current/mule-http.xsd">

    <http:listener-config name="HTTP_Listener_Configuration" host="0.0.0.0" port="9090" doc:name="HTTP Listener Configuration"/>

    <flow name="exampleFlow">
        <http:listener config-ref="HTTP_Listener_Configuration" path="/" allowedMethods="GET" doc:name="HTTP"/>
        <set-payload value="#[message.inboundProperties['http.query.params']['url_key']]" doc:name="Set Original Payload"/>

        <flow-ref name="exampleFlow2" doc:name="exampleFlow2"/>


        <choice doc:name="Choice">
            <when expression="#[flowVars['my_variable'].equals('var_value_1')]">
                <set-payload value="#['response_payload_1']" doc:name="Set Response Payload"/>
            </when>
            <otherwise>
                <set-payload value="#['response_payload_2']" doc:name="Set Response Payload"/>
            </otherwise>
        </choice>
    </flow>

    <flow name="exampleFlow2">
        <choice doc:name="Choice">
            <when expression="#['payload_1'.equals(payload)]">
                <flow-ref name="exampleSub_Flow1" doc:name="exampleSub_Flow1"/>
            </when>
            <otherwise>
                <flow-ref name="exampleSub_Flow2" doc:name="exampleSub_Flow2"/>
            </otherwise>
        </choice>
        </flow>

    <sub-flow name="exampleSub_Flow1">
        <set-variable variableName="my_variable" value="#['var_value_1']" doc:name="my_variable"/>
    </sub-flow>

    <sub-flow name="exampleSub_Flow2">
        <set-variable variableName="my_variable" value="#['var_value_2']" doc:name="my_variable"/>
    </sub-flow>
</mule>
```

The MUnit Generator is capable of produing the following:
```
<?xml version="1.0" encoding="UTF-8"?>

<mule xmlns="http://www.mulesoft.org/schema/mule/core" 
	xmlns:mock="http://www.mulesoft.org/schema/mule/mock" xmlns:munit="http://www.mulesoft.org/schema/mule/munit" 
	xmlns:doc="http://www.mulesoft.org/schema/mule/documentation" xmlns:spring="http://www.springframework.org/schema/beans" 
	xmlns:core="http://www.mulesoft.org/schema/mule/core" version="EE-3.7.3" 
	xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" 
	xsi:schemaLocation="http://www.mulesoft.org/schema/mule/mock 
        http://www.mulesoft.org/schema/mule/mock/current/mule-mock.xsd http://www.mulesoft.org/schema/mule/munit 
        http://www.mulesoft.org/schema/mule/munit/current/mule-munit.xsd http://www.springframework.org/schema/beans 
        http://www.springframework.org/schema/beans/spring-beans-current.xsd http://www.mulesoft.org/schema/mule/core 
        http://www.mulesoft.org/schema/mule/core/current/mule.xsd">
	<munit:config name="munit" doc:name="Munit Configuration"/>
	<spring:beans>
		<spring:import resource="classpath:example.xml"/>
	</spring:beans>

	<munit:test name="exampleFlow-test-1" description="Unit Test for exampleFlow">
		<mock:when doc:name="Mock" messageProcessor="mule:set-payload">
			<mock:with-attributes>
				<mock:with-attribute name="doc:name" whereValue="#['Set Original Payload']"/>
			</mock:with-attributes>
			<mock:then-return payload="#[]"/>
		</mock:when>
		<mock:when doc:name="Mock" messageProcessor="mule:flow">
			<mock:with-attributes>
				<mock:with-attribute name="name" whereValue="#['exampleFlow2']"/>
			</mock:with-attributes>
			<mock:then-return payload="#[]">
				<mock:invocation-properties>
					<mock:invocation-property key="" value=""/>
				</mock:invocation-properties>
			</mock:then-return>
		</mock:when>
		<flow-ref name="exampleFlow" doc:name="Flow-ref to exampleFlow"/>
		<munit:assert-payload-equals message="Incorrect payload!" expectedValue="#['response_payload_1']"/>
	</munit:test>

	<munit:test name="exampleFlow-test-2" description="Unit Test for exampleFlow">
		<mock:when doc:name="Mock" messageProcessor="mule:set-payload">
			<mock:with-attributes>
				<mock:with-attribute name="doc:name" whereValue="#['Set Original Payload']"/>
			</mock:with-attributes>
			<mock:then-return payload="#[]"/>
		</mock:when>
		<mock:when doc:name="Mock" messageProcessor="mule:flow">
			<mock:with-attributes>
				<mock:with-attribute name="name" whereValue="#['exampleFlow2']"/>
			</mock:with-attributes>
			<mock:then-return payload="#[]">
				<mock:invocation-properties>
					<mock:invocation-property key="" value=""/>
				</mock:invocation-properties>
			</mock:then-return>
		</mock:when>
		<flow-ref name="exampleFlow" doc:name="Flow-ref to exampleFlow"/>
		<munit:assert-payload-equals message="Incorrect payload!" expectedValue="#['response_payload_2']"/>
	</munit:test>

	<munit:test name="exampleFlow2-test-1" description="Unit Test for exampleFlow2">
		<munit:set payload="" doc:name="Set Initial Test Payload"/>
		<flow-ref name="exampleFlow2" doc:name="Flow-ref to exampleFlow2"/>
		<mock:verify-call messageProcessor="mule:sub-flow" doc:name="Verify Call" times="1">
			<mock:with-attributes>
				<mock:with-attribute name="name" whereValue="#[matchContains('exampleSub_Flow1')]"/>
			</mock:with-attributes>
		</mock:verify-call>
	</munit:test>

	<munit:test name="exampleFlow2-test-2" description="Unit Test for exampleFlow2">
		<munit:set payload="" doc:name="Set Initial Test Payload"/>
		<flow-ref name="exampleFlow2" doc:name="Flow-ref to exampleFlow2"/>
		<mock:verify-call messageProcessor="mule:sub-flow" doc:name="Verify Call" times="1">
			<mock:with-attributes>
				<mock:with-attribute name="name" whereValue="#[matchContains('exampleSub_Flow2')]"/>
			</mock:with-attributes>
		</mock:verify-call>
	</munit:test>

</mule>
```

You may notice that certain fields, such as ```<munit:set payload="" .../>``` and ```<mock:invocation-property key="" value=""/>``` were left blank by the generator. The end user will need to insert values where necessary to complete the MUnit test. I hope to work through this issue in future versions to allow for complete, functioning tests to be produced.
