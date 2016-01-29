# pylambda-login-alerter
A python function for AWS Lambda to receive CloudWatch Logs streams and alert 
via SNS when a succesfull SSH login is detected.

## Background

Direct SSH logins to instances is highly discouraged. To monitor SSH use in near real time, CloudWatch Logs 
receives key system logs from all instances. Creating a subscription from this Lambda function to your 
CloudWatch log streamwill send a SNS message for every succesfull SSH login. From SNS, these alerts can 
be forwarded to Slack, PagerDuty, Email, etc.

Sample filter for `/var/log/secure`: `[month, day, time, host, daemon=sshd*, accepted=Accepted,  ...]`

Current output message format includes:
- Source IP of the login
- Timestamp (from the host log)
- User ID logging in
- Hostname upon which the login is detected (from the host log)
- `project` tag of the host (defaults to `unknown` if not present)

## IAM Permissions Required

- sns-publish
- ec2 describe-tags

# References and Credits

This is loosely based upon the very useful patterns demonstrated at 
https://github.com/elelsee/pycfn-custom-resource and https://github.com/elelsee/pycfn-elasticsearch.
