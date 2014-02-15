zfs-snap-manager
================

ZFS Snapshot Manager

Usage
-----

All scripts are in the scripts folder. By executing manager.py, it deamonizes itself.

Configuration
-------------

The main configuration file is located in /etc and is called zfssnapmanager.cfg. It's an ini
file containing a section per volume that needs to be managed.

Example

    [zroot]
    mountpoint = /
    time = 21:00
    snapshot = True
    replicate_endpoint = ssh -p 2345 my.remote.server.org
    replicate_target = zpool/backups/zroot
    clean = True
    schema = 7d3w11m5y

A summary of the different options:

* mountpoint: Points to the location to which the volume is mounted.
* time: Can be either a timestamp in 24h notation after which a snapshot needs to be taken. It can also be 'trigger' indicating that it will take a snapshot as soon as a file with name '.trigger' is found in the volume's mountpoint. This can be used in case data is for example rsynced to the volume.
* snapshot: Indicates whether a snapshot should be taken or not. It might be possible that only cleaning needs to be executed if this volume is actually a target for another machine.
* replicate_endpoint: Can be left empty if replicating on localhost (e.g. copying snapshots to other pool). Should be omitted if no replication is required.
* replicate_target: The target to which the snapshots should be send. Should be omitted if no replication is required
* clean: A boolean indicating whether the snapshots should be cleaned up or not.
* schema: In case the snapshots should be cleaned, this is the schema the manager will use to clean.

Naming convention
-----------------

This script expects the snapshot names of a volume to be yyyymmdd. For pool/tank an
example snapshot name could be pool/tank@20131231

In case you don't want a snapshot to be managed by the script, just make sure it has
any other name, not matching this convention.

Buckets
-------

The system will use "buckets" to apply the GFS schema (Grandfather, Father, Son).
From every bucket, the oldest snapshot will be kept. At any given time the script is
executed, it will place the snapshots in their buckets, and then clean out all buckets.

Bucket schema
-------------

By default, the schema '7d3w11m4y' is followed, meaning:

* 7 daily buckets (starting from today)
* 3 weekly buckets (7 days a week)
* 11 monthly buckets (28 days a month)
* 4 yearly buckets (12 * 28 days a year)

This wraps up to 5 years (where a year is 12 * 28 days - so not mapping to a real year)

Other schema's are possible. One could for example only be intrested in keeping only the
snapshots for last week, in which the schema '7d0w0m0y' would be given. Any combination is possible.

Since from each bucket, the oldest snapshot is kept, snapshots will seem to "roll"
trough the buckets.

Warning
=======

As with any script deleting snapshots, use with caution. Make sure to test the script on
a dummy volume first. This to ensure no unexpected things will happen.

In case you find a bug, feel free to create a bugreport and/or fork and send a pull-request
in case you fixed the bug yourself.

[![githalytics.com alpha](https://cruel-carlota.pagodabox.com/a03f34b50aca0b3549e7ea7c82647ed6 "githalytics.com")](http://githalytics.com/khenderick/zfs-snap-manager)
