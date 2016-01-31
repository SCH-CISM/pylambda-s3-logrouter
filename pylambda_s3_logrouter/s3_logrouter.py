#!/bin/env python

# thanks to https://github.com/Kixeye/untar-to-s3/blob/master/untar-to-s3.py
# for parallel untar to S3 concepts

from __future__ import print_function
# import gevent
from gevent import monkey
monkey.patch_all()
from gevent.pool import Pool
import logging
import boto3
import json
import sys
import yaml
import os
import tarfile

logging.basicConfig()
log = logging.getLogger()
log.setLevel(logging.INFO)
logging.captureWarnings(True)

# Disable boto's default info logging. It's too voluminous.
logging.getLogger('boto3').setLevel(logging.WARN)

# fetch config settings
with open('config.yml', 'r') as f:
    config = yaml.load(f)
log.info("Config values: {}".format(config))


def __deploy_asset_to_s3(data, size, bucket, key):
    """Deploy a single asset file to an S3 bucket."""
    client = boto3.client('s3')
    try:
        logging.debug("Uploading %s (%s bytes)" % (key, size))
        client.put_object(Body=data, Bucket=bucket, Key=key,
                          ContentLength=size, 
                          ServerSideEncryption='AES256')

    except Exception as e:
        import traceback
        print(traceback.format_exc(e), file=sys.stderr)
        return 0

    # Return number of bytes uploaded.
    return size


def uncompress_and_copy(src_bucket, src_key, dst_bucket, dst_keyprefix='',
                        concurrency=50, strip_components=0):
    """Upload the contents of a tarball to the S3 bucket."""

    client = boto3.client('s3')
    tarfile_key = client.get_object(Bucket=src_bucket, Key=src_key)
    tarball_obj = tarfile_key['Body']

    # Open the tarball
    try:
        with tarfile.open(name=None, mode="r|*", fileobj=tarball_obj) as tarball:

            files_uploaded = 0

            # Parallelize the uploads so they don't take ages
            pool = Pool(concurrency)

            # Iterate over the tarball's contents.
            try:
                for member in tarball:

                    # Ignore directories, links, devices, fifos, etc.
                    if not member.isfile():
                        continue

                    # mimic the behavior of tar -x --strip-components=
                    stripped_name = member.name.split('/')[strip_components:]
                    if not bool(stripped_name):
                        continue

                    path = os.path.join(dst_keyprefix, '/'.join(stripped_name))

                    # Read file data from the tarball
                    fd = tarball.extractfile(member)

                    # Send a job to the pool.
                    pool.wait_available()
                    pool.apply_async(__deploy_asset_to_s3, (fd.read(), member.size,
                                                            dst_bucket,
                                                            path))

                    files_uploaded += 1

                # Wait for all transfers to finish
                pool.join()

            except KeyboardInterrupt:
                # Ctrl-C pressed
                print("Cancelling upload...")
                pool.join()

            finally:
                log.info("Uploaded %i files" % (files_uploaded))

    except tarfile.ReadError:
        print("Unable to read asset tarfile", file=sys.stderr)
        return

    return {'source': os.path.join(src_bucket, src_key),
            'destination': os.path.join(dst_bucket, dst_keyprefix),
            'files_sent': files_uploaded,
            'bytes_sent': 0}


def copy_only(src_bucket, src_key, dst_bucket, dst_key):
    """Copy an S3 object to a different location."""
    client = boto3.client('s3')
    client.copy_object(CopySource={'Bucket': src_bucket, 'Key': src_key},
                       Bucket=dst_bucket, Key=dst_key,
                       ServerSideEncryption='AES256')
    return {'source': os.path.join(src_bucket, src_key),
            'destination': os.path.join(dst_bucket, dst_key),
            'files_sent': 1},


def delete_key(bucket, key):
    """Return a given obkect from S3."""
    client = boto3.client('s3')
    result = client.delete_object(Bucket=bucket, Key=key)
    return result


def notify_status(topic, subject, message):
    """Send status message to SNS topic."""
    client = boto3.client('sns')
    message = json.dumps(message)
    client.publish(TopicArn=topic, Message=message, Subject=subject)
    return


def lambda_handler(event, context):
    """Primary event handler when running on Lambda."""
    log.info("Received event: {}".format(event))
    log.info("Event: {}".format(json.dumps(event)))

    context_json = context.__dict__
    context_json['remaining_time'] = context.get_remaining_time_in_millis()
    if 'identity' in context_json.keys():
        context_json.pop('identity')
    log.info("Context: {}".format(json.dumps(context_json)))

    # when receiving message via SNS, the S3 message must be extracted
    if 'Sns' in event['Records'][0]:
        event = json.loads(event['Records'][0]['Sns']['Message'])

    src_bucket = event['Records'][0]['s3']['bucket']['name']
    log.info("Source bucket: {}".format(src_bucket))
    src_key = event['Records'][0]['s3']['object']['key']
    log.info("Source key: {}".format(src_key))

    message = {'Results': []}

    result = uncompress_and_copy(src_bucket, src_key,
                                 config['dst']['bucket'],
                                 config['dst']['keyprefix'],
                                 strip_components=1,
                                 concurrency=100)
    message['Results'].append(result)
    notify_status(config['sns']['topic'], message=message, subject='LogRouter')

    return

if __name__ == "__main__":
    """Default action for interactive runs."""
    ch = logging.StreamHandler()
    ch.setLevel(logging.DEBUG)
    log.addHandler(ch)
    uncompress_and_copy('SRCBUCKET',
                        'SRCKEY',
                        'DSTBUCKET'
                        'DSTKEYPREFIX',
                        strip_components=1)
