#!/usr/bin/env python

import sys
from openstorage import api_pb2
from openstorage import api_pb2_grpc
from kubernetes import client, config, watch

# Get Portworx gRPC API
portworx_grpc = os.getenv('PWX_GRPC_ENDPOINT', 'localhost:9100')
print("Connecting to %s" % portworx_grpc)
channel = grpc.insecure_channel(portworx_grpc)

backup_cred = os.getenv('AWS_BACKUP_CRED_ID', None)

volume_id = sys.argv[1]

try:
    # Get status
    backups = api_pb2_grpc.OpenStorageCloudBackupStub(channel)
    status_resp = backups.Status(api_pb2.SdkCloudBackupStatusRequest(
        volume_id=volume_id
    ))
    backup_status = status_resp.statuses[volume_id]
    print('Status of the backup is {0}'.format(
        api_pb2.SdkCloudBackupStatusType.Name(backup_status.status)
    ))

    # Show history
    history = backups.History(api_pb2.SdkCloudBackupHistoryRequest(
        src_volume_id=volume_id
    ))
    print('Backup history for volume {0}'.format(volume_id))
    for item in history.history_list:
        print('Time:{0} Status:{1}'.format(
            item.timestamp.ToJsonString(),
            api_pb2.SdkCloudBackupStatusType.Name(item.status)
        ))

except grpc.RpcError as e:
    print('Failed: code={0} msg={1}'.format(e.code(), e.details()))
