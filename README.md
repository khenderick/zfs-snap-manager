zsnapd
======

ZFS Snapshot Daemon

A rework of ZFS Snapshot Manager by Kenneth Henderick <kenneth@ketronic.be>

ZFS dataset configuration file /etc/zfssnapmanager.cfg should be upwards compatible with /etc/zsnapd/datasets.conf.

Usage
-----

All the functional code is in the scripts folder.  Execute zsnapd, it deamonizes itself.

Features
--------

* Fully Python3 based
* Native Systemd daemon compitability via py-magcode-core python daemon and logging support library
* Debug command line switch and stderr logging
* Systemd journalctl logging.
* Full standard Unix daemon support via py-magcode-core, with logging to syslog or logfile
* Configuration is stored in single configuration file with the ini file format
* Triggers the configured actions based on time or a '.trigger' file present in the dataset's mountpoint.
* Can take snapshots (with a yyyymmdd timestamp format)
* Can replicate snapshots to/from other nodes
  * Push based when the replication source has access to the replication target
  * Pull based when the replication source has no access to the replication target. Typically when you don't want to give
    all nodes access to the backup/replication target
* Cleans all snapshots with the yyyymmdd timestamp format based on a GFS schema (Grandfather, Father, Son).
* Supports pre and post commands
  * Pre command is executed before any action is executed
  * Post command is executed after the actions are executed, but before cleaning

Configuration
-------------

The daemon configuration file is in /etc/zsnapd/process.conf in ini format and a sample is as follows:

		[DEFAULT]
		run_as_user = root

		[zsnapd]
		# Use following setting to check daemon reconfiguring
		daemon_canary = blau
		debug_mark = True
		# Both below in seconds
		sleep_time = 300
		debug_sleep_time = 15
    # dataset configuration file
    # dataset_config_file = /etc/zsnapd/datasets.conf
    # dataset_config_file = /etc/zfssnapmanager.cfg
		# Uncomment to set up syslog logging
		# see pydoc3 syslog and man 3 syslog for value names with 'LOG_'
		# prefix stripped
		#syslog_facility = DAEMON
		#syslog_level = INFO
		# Uncomment to set up file logging
		#log_file = /var/log/zsnapd.log
		#log_file_max_size_kbytes = 1024
		#log_file_backup_count = 7

Adjust sleep_time (in seconds) to set interval zsnapd runs code.  For 30 minute intervals, set to
1800 seconds.

Command line arguments to zsnapd are:

		Usage: zsnapd [-dhv] [-c config_file]

			ZFS Snap Managment Daemon

			-c, --config-file       set configuration file
			-d, --debug             set debug level {0-3|none|normal|verbose|extreme}
			-h, --help              help message
			-b, --memory-debug      memory debug output
			-S, --systemd           Run as a systemd daemon, no fork
			-v, --verbose           verbose output
			-r, --rpdb2-wait        Wait for rpdb2 (seconds)

Note the default configuration file is /etc/zsnapd/process.conf, and systemd native mode is via the
--systemd switch

The dataset configuration file is located in /etc/zsnapd and is called datasets.conf. It's an ini
file containing a section per dataset/volume that needs to be managed.

Examples

    [zroot]
    mountpoint = /
    time = 21:00
    snapshot = True
    replicate_endpoint = ssh -p 2345 my.remote.server.org
    replicate_target = zpool/backups/zroot
    schema = 7d3w11m5y
    compression = gzip

    [zpool/data]
    mountpoint = /mnt/data
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

    [zpool/backups/data]
    mountpoint = /mnt/backups/data
    time = 23:00
    snapshot = False
    replicate_endpoint = ssh other.remote.server.org
    replicate_source = zpool/data
    schema = 7d3w11m4y

A summary of the different options:

* mountpoint: Points to the location to which the dataset is mounted, None for volumes
* time: Can be either a timestamp in 24h notation after which a snapshot needs to be taken. It can also be 'trigger' indicating that it will take a snapshot as soon as a file with name '.trigger' is found in the dataset's mountpoint. This can be used in case data is for example rsynced to the dataset.
* snapshot: Indicates whether a snapshot should be taken or not. It might be possible that only cleaning needs to be executed if this dataset is actually a replication target for another machine.
* replicate_endpoint: Can be left empty if replicating on localhost (e.g. copying snapshots to other pool). Should be omitted if no replication is required.
* replicate_target: The target to which the snapshots should be send. Should be omitted if no replication is required or a replication_source is specified.
* replicate_source: The source from which to pull the snapshots to receive onto the local dataset. Should be omitted if no replication is required or a replication_target is specified.
* compression: Indicates the compression program to pipe remote replicated snapshots through (for use in low-bandwidth setups.) The compression utility should accept standard compression flags (`-c` for standard output, `-d` for decompress.)
* schema: In case the snapshots should be cleaned, this is the schema the manager will use to clean.
* preexec: A command that will be executed, before snapshot/replication. Should be omitted if nothing should be executed
* postexec: A command that will be executed, after snapshot/replication,  but before the cleanup. Should be omitted if nothing should be executed

Naming convention
-----------------

This script's snapshot will always given a timestamp (format yyyymmdd) as name. For pool/tank an
example snapshot name could be pool/tank@20131231

All snapshots are currently used for replication (both snapshots taken by the script as well as snapshots taken by
other means (other scripts or manually), regardless of their name.

However, the script will only clean snapshots with the timestamp naming convention. In case you don't want a snapshot to
be cleaned by the script, just make sure it has any other name, not matching this convention.

Buckets
-------

The system will use "buckets" to apply the GFS schema.
From every bucket, the oldest snapshot will be kept. At any given time the script is
executed, it will place the snapshots in their buckets, and then clean out all buckets.

Bucket schema
-------------

For example, the schema '7d3w11m4y' means:

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
* A laptop, having a single root ZFS setup, containing 2 normal filesystems and a ZFS dataset
* A local NAS with lots of data and the replication target of most systems
* A remote NAS (used as normal NAS by these people) used with two-way replication as offsite backup setup.

Dependencies
------------

This python program/script has a few dependencies. When using the Archlinux AUR, these will be installed automatically.

* zfs
* python3
* openssh
* mbuffer
* python3-magcode-core > 1.4.10 - on pypi.org
* python3-psutil
* python3-setproctitle

Logging
-------

The script is logging into systemd journals, and /var/log/syslog

License
-------

This program/script is licensed under MIT, which basically means you can do anything you want with it. You can find
the license text in the 'LICENSE' file.

If you like the software or if you're using it, feel free to leave a star as a toke of appreciation.

Warning
-------

As with any script deleting snapshots, use with caution. Make sure to test the script on
a dummy dataset first when you use it directly from the repo. This to ensure no unexpected things will happen.

The releases should be working fine, as I use these on my own environment.

In case you find a bug, feel free to create a bugreport and/or fork and send a pull-request
in case you fixed the bug yourself.

Packages
--------

ZFS Snapshot Manager is available in the following distributions:

* ArchLinux: https://aur.archlinux.org/packages/zfs-snap-manager (AUR)
  * The PKGBUILD and install scripts are now available through the AUR git repo

zsnapd is available in following distributions:

* Debian: http://packages.debian.org as part of the main repostitory
* Ubuntu (eventually)

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
