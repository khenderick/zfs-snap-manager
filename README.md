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

Examples

    [zroot]
    mountpoint = /
    time = 21:00
    snapshot = True
    replicate_endpoint = ssh -p 2345 my.remote.server.org
    replicate_target = zpool/backups/zroot
    schema = 7d3w11m5y

    [zpool/tank]
    mountpoint = /mnt/mytank
    time = trigger
    snapshot = True
    schema = 5d0w0m0y
    preexec = echo "starting" | mail somebody@example.com
    postexec = echo "finished" | mail somebody@exampe.com

    [zpool/myzvol]
    mountpoint = None
    time = 21:00
    snapshot = True
    schema = 7d3w0m0y

A summary of the different options:

* mountpoint: Points to the location to which the volume is mounted.
* time: Can be either a timestamp in 24h notation after which a snapshot needs to be taken. It can also be 'trigger' indicating that it will take a snapshot as soon as a file with name '.trigger' is found in the volume's mountpoint. This can be used in case data is for example rsynced to the volume.
* snapshot: Indicates whether a snapshot should be taken or not. It might be possible that only cleaning needs to be executed if this volume is actually a target for another machine.
* replicate_endpoint: Can be left empty if replicating on localhost (e.g. copying snapshots to other pool). Should be omitted if no replication is required.
* replicate_target: The target to which the snapshots should be send. Should be omitted if no replication is required.
* schema: In case the snapshots should be cleaned, this is the schema the manager will use to clean.
* preexec: A command that will be executed, before snapshot/replication. Should be omitted if nothing should be executed
* postexec: A command that will be executed, after snapshot/replication,  but before the cleanup. Should be omitted if nothing should be executed

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

Examples
--------

The examples directory contains 3 example configuration files, almost identical as my own 'production' setup.

* A non-ZFS device (router), rsyncing its filesystem to an NFS shared dataset.
* A laptop, having a single root ZFS setup, containing 2 normal filesystems and a ZFS volume
* A local NAS with lots of data and the replication target of most systems
* A remote NAS (used as normal NAS by these people) used with two-way replication as offsite backup setup.

Dependencies
------------

This python program/script has a few dependencies. When using the Archlinux AUR, these will be installed automatically.

* zfs
* python2
* openssh
* mbuffer
* python2-daemon

Logging
-------

The script is logging into /var/log/zfs-snap-manager.log

License
-------

This program/script is licensed under MIT, which basically means you can do anything you want with it. You can find
the license text in the 'LICENSE' file.

If you like the software or if you're using it, feel free to leave a star as a toke of appreciation.

Warning
-------

As with any script deleting snapshots, use with caution. Make sure to test the script on
a dummy volume first. This to ensure no unexpected things will happen.

In case you find a bug, feel free to create a bugreport and/or fork and send a pull-request
in case you fixed the bug yourself.

ZFS
---

From Wikipedia:

    ZFS is a combined file system and logical volume manager designed by Sun Microsystems.
    The features of ZFS include protection against data corruption, support for high storage capacities,
    efficient data compression, integration of the concepts of filesystem and volume management, snapshots
    and copy-on-write clones, continuous integrity checking and automatic repair, RAID-Z and native NFSv4 ACLs.

    ZFS was originally implemented as open-source software, licensed under the Common Development and
    Distribution License (CDDL). The ZFS name is registered as a trademark of Oracle Corporation.

ZFS Snapshot Manager is a standalone project, and is not affiliated with ZFS or Oracle Corporation.
