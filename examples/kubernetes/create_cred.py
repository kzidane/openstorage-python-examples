#!/usr/bin/env python

import os
import grpc
from openstorage import api_pb2
from openstorage import api_pb2_grpc

portworx_grpc = os.getenv('PWX_GRPC_ENDPOINT', 'localhost:9100')
print "Connecting to %s" % portworx_grpc
channel = grpc.insecure_channel(portworx_grpc)
access_key = os.getenv('AWS_ACCESS_KEY', None)
secret_key = os.getenv('AWS_SECRET_KEY', None)
endpoint = os.getenv('AWS_S3_ENDPOINT', 's3.us-west-2.amazonaws.com')
region = os.getenv('AWS_REGION', 'us-west-2')

try:
    # Create a credentials
    creds = api_pb2_grpc.OpenStorageCredentialsStub(channel)
    cred_resp = creds.Create(api_pb2.SdkCredentialCreateRequest(
        name='aws',
        aws_credential=api_pb2.SdkAwsCredentialRequest(
            access_key=access_key,
            secret_key=secret_key,
            endpoint=endpoint,
            region=region
        )
    ))
    print('Credential id is {0}'.format(cred_resp.credential_id))

except grpc.RpcError as e:
    print('Failed: code={0} msg={1}'.format(e.code(), e.details()))
