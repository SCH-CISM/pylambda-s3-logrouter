#!/bin/env python

# thanks to https://github.com/Kixeye/untar-to-s3/blob/master/untar-to-s3.py
# for parallel untar to S3 concepts

import logging
log = logging.getLogger()
log.setLevel(logging.INFO)

import boto3
import json
import zlib
import base64
import datetime
import yaml
import gevent
from gevent import monkey; monkey.patch_all()
from gevent.pool import Pool

logging.captureWarnings(True)

with open('config.yaml', 'r') as f:
    config = yaml.load(f)
log.info("Config values: {}".format(config))


def __deploy_asset_to_s3(data, path, size, bucket, compress=True):
    """Deploy a single asset file to an S3 bucket."""
    try:
        headers = {
            'Content-Type': mimetypes.guess_type(path)[0],
            'Cache-Control': "public, max-age=31536000",
            'Content-Length': size,
        }

        # gzip the file if appropriate
        if mimetypes.guess_type(path)[0] in COMPRESSIBLE_FILE_TYPES and compress:
            new_buffer = io.BytesIO()
            gz_fd = gzip.GzipFile(compresslevel=9, mode="wb", fileobj=new_buffer)
            gz_fd.write(data)
            gz_fd.close()

            headers['Content-Encoding'] = 'gzip'
            headers['Content-Length'] = new_buffer.tell()

            new_buffer.seek(0)
            data = new_buffer.read()

        logging.debug("Uploading %s (%s bytes)" % (path, headers['Content-Length']))
        key = bucket.new_key(path)
        key.set_contents_from_string(data, headers=headers, policy='public-read', replace=True,
                                     reduced_redundancy=False)

    except Exception as e:
        import traceback
        print(traceback.format_exc(e), file=sys.stderr)
        return 0

    # Return number of bytes uploaded.
    return headers['Content-Length']


def deploy_tarball_to_s3(tarball_obj, bucket_name, prefix='', region='us-west-2', concurrency=50, no_compress=False, strip_components=0):
    """
    Upload the contents of `tarball_obj`, a File-like object representing a valid .tar.gz file, to the S3 bucket `bucket_name`
    """
    # Connect to S3 and get a reference to the bucket name we will push files to
    client = boto3.client('s3')

    # Open the tarball
    try:
        with tarfile.open(name=None, mode="r:*", fileobj=tarball_obj) as tarball:

            files_uploaded = 0

            # Parallelize the uploads so they don't take ages
            pool = Pool(concurrency)

            # Iterate over the tarball's contents.
            try:
                for member in tarball:

                    # Ignore directories, links, devices, fifos, etc.
                    if not member.isfile():
                        continue

                    # Mimic the behaviour of tar -x --strip-components=
                    stripped_name = member.name.split('/')[strip_components:]
                    if not bool(stripped_name):
                        continue

                    path = os.path.join(prefix, '/'.join(stripped_name))

                    # Read file data from the tarball
                    fd = tarball.extractfile(member)

                    # Send a job to the pool.
                    pool.wait_available()
                    pool.apply_async(__deploy_asset_to_s3, (fd.read(), path, member.size, bucket, not no_compress))

                    files_uploaded += 1

                # Wait for all transfers to finish
                pool.join()

            except KeyboardInterrupt:
                # Ctrl-C pressed
                print("Cancelling upload...")
                pool.join()

            finally:
                print("Uploaded %i files" % (files_uploaded))

    except tarfile.ReadError:
        print("Unable to read asset tarfile", file=sys.stderr)
        return

def copy_only(src_bucket, src_key, dst_bucket, dst_key):
    """Copy an S3 object to a different location."""
    log.info("Fetching tags for instance: {}".format(instance_id))
    client = boto3.client('s3')
    result =client.copy_object(CopySource={'Bucket': src_bucket, 'Key': src_key}, 
                               Bucket=dst_bucket, Key=dst_key,
                               ServerSideEncryption='AES256')
    return result


def uncompress_and_copy(bucket, key):
    """Return an array of tags for a given instance id."""
    log.info("Fetching tags for instance: {}".format(instance_id))
    client = boto3.client('s3')
    return clean_tags


def delete_key(bucket, key):
    """Return an array of tags for a given instance id."""
    log.info("Fetching tags for instance: {}".format(instance_id))
    client = boto3.client('s3')
    result = client.delete_object(Bucket=bucket, Key=key)
    return result


def notify_success(bucket, key):
    """Return an array of tags for a given instance id."""
    log.info("Fetching tags for instance: {}".format(instance_id))
    client = boto3.client('sns')
    return clean_tags

def lambda_handler(event, context):
    """Primary event handler when running on Lambda."""
    log.info("Received event: {}".format(event))
    log.info("Event: {}".format(json.dumps(event)))

    client = boto3.client('s3')

    context_json = context.__dict__
    context_json['remaining_time'] = context.get_remaining_time_in_millis()
    if 'identity' in context_json.keys():
        context_json.pop('identity')
    log.info("Context: {}".format(json.dumps(context_json)))

    src_bucket = event.Records[0].s3.bucket.name
    log.info("Source bucket: {}".format(src_bucket))
    src_key = event.Records[0].s3.object.key
    log.info("Source key: {}".format(src_key))

    copy_only(src_bucket, src_key, emr_bucket, emr_keyprefix)
    uncompress_and_copy(src_bucket, src_key, elk_bucket, elk_keyprefix)
    delete_key(src_bucket, src_key)
    notify_status(src_bucket, src_key)

    return

if __name__ == "__main__":
    """Default action for interactive runs."""
    ch = logging.StreamHandler()
    ch.setLevel(logging.DEBUG)
    log.addHandler(ch)
