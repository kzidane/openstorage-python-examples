#!/usr/bin/env python

import os
import grpc
from openstorage import api_pb2
from openstorage import api_pb2_grpc

portworx_grpc = os.getenv('PWX_GRPC_ENDPOINT', 'localhost:9100')
print("Connecting to %s" % portworx_grpc)
channel = grpc.insecure_channel(portworx_grpc)

try:
    # Cluster connection
    clusters = api_pb2_grpc.OpenStorageClusterStub(channel)
    ic_resp = clusters.InspectCurrent(api_pb2.SdkClusterInspectCurrentRequest())
    print('Connected to {0} with status {1}'.format(
        ic_resp.cluster.id,
        api_pb2.Status.Name(ic_resp.cluster.status)
    ))

    # List Volumes
    volumes = api_pb2_grpc.OpenStorageVolumeStub(channel)
    vols = volumes.Enumerate(api_pb2.SdkVolumeEnumerateRequest())
    for vol in vols.volume_ids:
        print('Volume id vol: {0}'.format(vol))

except grpc.RpcError as e:
    print('Failed: code={0} msg={1}'.format(e.code(), e.details()))
