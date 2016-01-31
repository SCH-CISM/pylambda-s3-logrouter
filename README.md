# pylambda-s3-logrouter

A python function for AWS Lambda to route incoming log bundles to the various
consuming processes.

## Background

Several processes consume log files received from on-premises systems via
batched upload. This Lambda function receives S3 events from the upload
location, extracts tar files into the component parts, and uploads them with
SSE to a configured destination location in S3. Upon completion, a message of
results are sent to a SNS topic.

This Lambda function can receive S3 events either via SNS or directly from S3.

Output message format includes:
- Source file
- Destination bucket and prefix
- Number of files copied to destination
- Bytes copied to destination (not currently working)

## Required IAM Permissions

This lambda function must have the following permissions:
- s3::get-object
- s3::put-object
- sns::publish

## Configuration

A config.yml file has two sections of parameters

| Section | Parameter | Value                                     |
|---------|-----------|-------------------------------------------|
| dst     | bucket    | destination bucket                        |
| dst     | prefix    | key prefix to place files                 |
| sns     | topic     | SNS topic ARN to send completion messages |

Current testing shows a Lambda function with 768MB of memory and an execution
timeout of 5 minutes is required for successful completion.

## Compiling

The `build_lambda_function.sh` script creates a ZIP file for deploying to 
AWS Lambda. The `config.yml` file is bundled with the function and must be 
configured prior to building.

## References and Credits

Parallel tar extract concept adapted from 
https://github.com/Kixeye/untar-to-s3/blob/master/untar-to-s3.py.

General Lambda principals loosed based upon the very useful patterns 
demonstrated at https://github.com/elelsee/pycfn-custom-resource and 
https://github.com/elelsee/pycfn-elasticsearch.
