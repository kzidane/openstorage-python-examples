#!/usr/bin/env python

import os
import grpc
import json
from openstorage import api_pb2
from openstorage import api_pb2_grpc
import requests
import getpass

def yes_or_no(question):
    while "the answer is invalid":
        reply = str(raw_input(question+' (y/n): ')).lower().strip()
        if reply[0] == 'y':
            return True
        if reply[0] == 'n':
            return False

OKTA_ENDPOINT = os.getenv('PWX_OKTA_ENDPOINT',
 'https://dev-399155.okta.com/oauth2/default/v1/token')

print("Using OIDC Endpoint: %s" % OKTA_ENDPOINT)
if not yes_or_no("Is this OIDC Endpoint OK?"):
    exit(0)

client_id = raw_input("What is the client id for the OIDC? ")
client_secret = getpass.getpass("What is the Client Secret for the OIDC? ")
username = raw_input("What is your Username? ")
password = getpass.getpass('What is your Password:')

PARAMS = {
   'client_id': client_id,
   'client_secret': client_secret,
   'grant_type': "password",
   'redirect_uri': "localhost:8080",
   'username': username,
   'password': password,
   'scope': "openid profile email"

} 

# sending get request and saving the response as response object 
r = requests.post(url = OKTA_ENDPOINT, data = PARAMS) 
  
# extracting data in json format 
data = r.json()
openid_token = data[u'id_token']
print("Retrieved your token: %s " % openid_token)

portworx_grpc = os.getenv('PWX_GRPC_ENDPOINT', 'localhost:9100')
portworx_cafile = os.getenv('PWX_CA_FILE', '')
print("Connecting to %s" % portworx_grpc)

def get_channel(address, cafile, token, opts=None):
    if cafile == '':
            return grpc.insecure_channel(address, opts)
    else:
        with open(cafile, 'rb') as f:
            capem = f.read()
        creds = grpc.ssl_channel_credentials(root_certificates=capem)
        if token != '':
            auth = grpc.access_token_call_credentials(token)
            return grpc.secure_channel(address, grpc.composite_channel_credentials(creds, auth), opts)
        else:
            return grpc.secure_channel(address, creds, opts)

channel = get_channel(portworx_grpc, portworx_cafile, openid_token)

md = []
# use the following method to use tokens on insecure connections
if openid_token != '' and portworx_cafile == '':
    md.append(("authorization", "bearer "+openid_token))

try:
    # Cluster connection
    clusters = api_pb2_grpc.OpenStorageClusterStub(channel)
    ic_resp = clusters.InspectCurrent(api_pb2.SdkClusterInspectCurrentRequest(), metadata=md)
    print('Connected to {0} with status {1}'.format(
        ic_resp.cluster.id,
        api_pb2.Status.Name(ic_resp.cluster.status)
    ))
    
    vol_name = raw_input("What is the name of your volume? ")
    halevel = raw_input("What is the ha_level of your volume? ")

    # Create a volume
    volumes = api_pb2_grpc.OpenStorageVolumeStub(channel)
    v_resp = volumes.Create(api_pb2.SdkVolumeCreateRequest(
        name=vol_name,
        spec=api_pb2.VolumeSpec(
            size=100*1024*1024*1024,
            ha_level=int(halevel),
            format=api_pb2.FS_TYPE_EXT4,
        )
    ), metadata=md)
    print('Volume id is {0}'.format(v_resp.volume_id))

except grpc.RpcError as e:
    print('Failed: code={0} msg={1}'.format(e.code(), e.details()))
