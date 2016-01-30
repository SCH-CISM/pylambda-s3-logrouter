# pylambda-s3-logrouter
A python function for AWS Lambda to route incoming log bundles to the various consuming processes

## Background

Several processes consume log files received from on-premises systems via batched upload. This Lambda 
function receives S3 events from the upload location, extracts tar files into the component parts, 
and uploads them to the various processes input locations on S3. Upon completion, a message of results are 
sent to a SNS topic.

Current output message format includes:
- Source file
- Destination bucket and prefix
- Number of files copied

## IAM Permissions Required

- sns::publish
- s3::get-object
- s3::put-object
- s3::put-object-acl

## Configuration

A config.yml file has three sections of parameters
- ELK (bucket and prefix)
- EMR (bucket and prefix)
- SNS Topic ARN

Current testing shows a Lambda function with 1,024MB of memory and an execution 
timeout of 5 minutes is required for successful completion.

# References and Credits

This is loosely based upon the very useful patterns demonstrated at 
https://github.com/elelsee/pycfn-custom-resource and https://github.com/elelsee/pycfn-elasticsearch.
