#!/usr/bin/env python

import os
import grpc
import asyncio
import signal
import sys
from datetime import datetime
from openstorage import api_pb2
from openstorage import api_pb2_grpc
from kubernetes import client, config, watch

# Get Portworx gRPC API
portworx_grpc = os.getenv('PWX_GRPC_ENDPOINT', 'localhost:9100')
print("Connecting to %s" % portworx_grpc)
channel = grpc.insecure_channel(portworx_grpc)

# Configs can be set in Configuration class directly or using helper utility
kubeconfig = os.getenv('KUBECONFIG_FILE', '~/.kube/kubeconfig')
backup_cred = os.getenv('AWS_BACKUP_CRED_ID', None)
config.load_kube_config(config_file=kubeconfig)

v1 = client.CoreV1Api()
w = watch.Watch()
loop = asyncio.get_event_loop()
pvcs_action_taken = []

# A asynchronous function to do some work
@asyncio.coroutine
def px_create_snapshot(portworx_volume_id, pvc_name):
    try:
        print("Creating a snapshot per company policy of %s!" % portworx_volume_id)
        # Create a snapshot
        volumes = api_pb2_grpc.OpenStorageVolumeStub(channel)
        snap = volumes.SnapshotCreate(api_pb2.SdkVolumeSnapshotCreateRequest(
         volume_id=portworx_volume_id,
         name="%s-%s" % (pvc_name,"{:%B-%d-%Y-%s}".format(datetime.now()))
        ))
        print('Snapshot created with id {0}'.format(snap.snapshot_id))
    except grpc.RpcError as e:
        print('Failed: code={0} msg={1}'.format(e.code(), e.details()))

# A asynchronous function to do some work
@asyncio.coroutine
def px_create_cloud_backup(portworx_volume_id, backup_cred):
    if backup_cred is not None:
        try:
            # Create backup
            backups = api_pb2_grpc.OpenStorageCloudBackupStub(channel)
            backup_resp = backups.Create(api_pb2.SdkCloudBackupCreateRequest(
                volume_id=portworx_volume_id,
                credential_id=cred_resp.credential_id,
                full=False
            ))
        except grpc.RpcError as e:
            print('Failed: code={0} msg={1}'.format(e.code(), e.details()))
    else:
        print('Failed, no backup credential set')

def signal_handler(sig, frame):
        print('You pressed Ctrl+C!')
        w.stop()
        loop.close()
        sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)

# Only watch events related to Persistent Volumes
for event in w.stream(v1.list_persistent_volume, _request_timeout=(30,None)):
    # Let's only look at "new" ADDED volumes.
    if event['type'] == "ADDED":
        # Let's make sure Portworx provisioning this volume
        if event['object'].metadata.annotations['kubernetes.io/createdby'] == "portworx-volume-dynamic-provisioner":
                # Have we already taken action on this pvc?
                pvc = event['object'].metadata.name
                if pvc not in pvcs_action_taken:
                    px_vol_id = event['object'].spec.portworx_volume.volume_id
                    print("Found a new pvc: %s px-volume: %s" % (pvc, px_vol_id))
                    print("We're going to do thing using the portworx SDK!")
                    # Create a snapshot
                    tasks = [
                        asyncio.ensure_future(px_create_snapshot(px_vol_id, pvc)),
                        asyncio.ensure_future(px_create_cloud_backup(px_vol_id, backup_cred))]
                    loop.run_until_complete(asyncio.wait(tasks))
                    # Add PVC to the list of PVCs we've taken action on
                    pvcs_action_taken.append(pvc)
