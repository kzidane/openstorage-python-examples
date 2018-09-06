# Python OpenStorage SDK Examples

## Setup

```
$ mkvirtualenv python-openstorage
New python executable in ...
Also creating executable in ...
Installing setuptools, pip, wheel...done.

$ (python-openstorage) - pip install grpcio grpcio-tools
```

## Test connection

### Run Mock Server

First, run the openstorage Mock Server
```
docker run --rm --name sdk -d -p 9100:9100 -p 9110:9110 openstorage/mock-sdk-server
```

Next, test a connection to the mock server from the Python interpreter.
```
python
Python 2.7.15 (default, Jun 17 2018, 12:46:58)
[GCC 4.2.1 Compatible Apple LLVM 9.1.0 (clang-902.0.39.2)] on darwin
Type "help", "copyright", "credits" or "license" for more information.
>>> import grpc
>>> from openstorage import api_pb2
>>> from openstorage import api_pb2_grpc
>>> channel = grpc.insecure_channel('localhost:9100')
>>> try:
    # Cluster connection
    clusters = api_pb2_grpc.OpenStorageClusterStub(channel)
    ic_resp = clusters.InspectCurrent(api_pb2.SdkClusterInspectCurrentRequest())
    print('Connected to {0} with status {1}'.format(
        ic_resp.cluster.id,
        api_pb2.Status.Name(ic_resp.cluster.status)
    ))
except grpc.RpcError as e:
    print('Failed: code={0} msg={1}'.format(e.code(), e.details()))

Connected to ce6b309e289d620be08c964969aeb39f with status STATUS_OK
>>>
```

### Run a test app against the Mock Server

```
$  python app.py
Connected to ce6b309e289d620be08c964969aeb39f with status STATUS_OK
Volume id is 92ebbfd8-f35c-4e5b-90b6-b0c2377cac21
Snapshot created with id 4cd44336-834c-45ab-8c3e-39594873bb08
Credential id is e0e50090-6265-4681-a0ef-9458b19e42cc
Status of the backup is SdkCloudBackupStatusTypeDone
Backup history for volume 92ebbfd8-f35c-4e5b-90b6-b0c2377cac21
Time:2018-09-06T21:24:22.974003800Z Status:SdkCloudBackupStatusTypeDone
```
