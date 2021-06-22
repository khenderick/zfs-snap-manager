#!/usr/bin/python2
# Copyright (c) 2014 Kenneth Henderick <kenneth@ketronic.be>
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.

"""
Provides the overal functionality
"""

import ConfigParser
import time
import os
import logging
import logging.handlers
from datetime import datetime,timedelta

from zfs import ZFS
from clean import Cleaner
from helper import Helper


BUFFER_SIZE = '512M' # Default -m value to pass to mbuffer


class Manager(object):
    """
    Manages the ZFS snapshotting process
    """

    logger = None  # To be overwritten by Manager.init_logger()

    @staticmethod
    def init_logger():
        """
        Initializes the log handler, storing the logger object as static property
        """

        log_filename = '/var/log/zfs-snap-manager.log'
        formatter = logging.Formatter('%(asctime)s - %(message)s')
        handler = logging.handlers.RotatingFileHandler(log_filename, maxBytes=1024 * 1024, backupCount=2)
        handler.setFormatter(formatter)

        Manager.logger = logging.getLogger('logger')
        Manager.logger.setLevel(logging.INFO)
        Manager.logger.addHandler(handler)
        Cleaner.logger = Manager.logger  # Pass logger along
        ZFS.logger = Manager.logger  # Pass logger along

    @staticmethod
    def run(settings):
        """
        Executes a single run where certain datasets might or might not be snapshotted
        """

        now = datetime.now()
        yda = datetime.now() - timedelta(1)
        today = '{0:04d}{1:02d}{2:02d}'.format(now.year, now.month, now.day)
        yesterday = '{0:04d}{1:02d}{2:02d}'.format(yda.year, yda.month, yda.day)

        snapshots = ZFS.get_snapshots()
        datasets = ZFS.get_datasets()
        for dataset in datasets:
            if dataset in settings:
                try:
                    dataset_settings = settings[dataset]
                    local_snapshots = snapshots.get(dataset, [])

                    take_snapshot = dataset_settings['snapshot'] is True
                    replicate = dataset_settings['replicate'] is not None

                    # Decide whether we need to handle this dataset
                    execute = False
                    if take_snapshot is True or replicate is True:
                        if dataset_settings['time'] == 'trigger':
                            # We wait until we find a trigger file in the filesystem
                            trigger_filename = '{0}/.trigger'.format(dataset_settings['mountpoint'])
                            if os.path.exists(trigger_filename):
                                Manager.logger.info('Trigger found on {0}'.format(dataset))
                                os.remove(trigger_filename)
                                execute = True
                        else:
                            trigger_time = dataset_settings['time'].split(':')
                            hour = int(trigger_time[0])
                            minutes = int(trigger_time[1])
                            if (now.hour > hour or (now.hour == hour and now.minute >= minutes)) and today not in local_snapshots:
                                Manager.logger.info('Time passed for {0}'.format(dataset))
                                execute = True

                    if execute is True:
                        # Pre exectution command
                        if dataset_settings['preexec'] is not None:
                            Helper.run_command(dataset_settings['preexec'], '/')

                        if take_snapshot is True:
                            # Take today's snapshotzfs
                            Manager.logger.info('Taking snapshot {0}@{1}'.format(dataset, today))
                            ZFS.snapshot(dataset, today, dataset_settings['recursive'])
                            local_snapshots.append(today)
                            Manager.logger.info('Taking snapshot {0}@{1} complete'.format(dataset, today))

                        # Replicating, if required
                        if replicate is True:
                            Manager.logger.info('Replicating {0}'.format(dataset))
                            replicate_settings = dataset_settings['replicate']
                            push = replicate_settings['target'] is not None
                            remote_dataset = replicate_settings['target'] if push else replicate_settings['source']
                            remote_snapshots = ZFS.get_snapshots(remote_dataset, replicate_settings['endpoint'])
                            last_common_snapshot = None
                            if remote_dataset in remote_snapshots:
                                if push is True:  # If pushing, we search for the last local snapshot that is remotely available
                                    for snapshot in local_snapshots:
                                        if snapshot in remote_snapshots[remote_dataset]:
                                            last_common_snapshot = snapshot
                                else:  # Else, we search for the last remote snapshot that is locally available
                                    for snapshot in remote_snapshots[remote_dataset]:
                                        if snapshot in local_snapshots:
                                            last_common_snapshot = snapshot
                            if last_common_snapshot is not None:  # There's a common snapshot
                                previous_snapshot = None
                                if push is True:
                                    for snapshot in local_snapshots:
                                        if snapshot == last_common_snapshot:
                                            previous_snapshot = last_common_snapshot
                                            continue
                                        if previous_snapshot is not None:
                                            # There is a snapshot on this host that is not yet on the other side.
                                            size = ZFS.get_size(dataset, previous_snapshot, snapshot)
                                            Manager.logger.info('  {0}@{1} > {0}@{2} ({3})'.format(dataset, previous_snapshot, snapshot, size))
                                            ZFS.replicate(dataset, previous_snapshot, snapshot, remote_dataset, replicate_settings.get('buffer_size', BUFFER_SIZE), replicate_settings['endpoint'], direction='push', compression=replicate_settings['compression'])
                                            ZFS.hold(dataset, snapshot)
                                            ZFS.hold(remote_dataset, snapshot, replicate_settings['endpoint'])
                                            ZFS.release(dataset, previous_snapshot)
                                            ZFS.release(remote_dataset, previous_snapshot, replicate_settings['endpoint'])
                                            previous_snapshot = snapshot
                                else:
                                    for snapshot in remote_snapshots[remote_dataset]:
                                        if snapshot == last_common_snapshot:
                                            previous_snapshot = last_common_snapshot
                                            continue
                                        if previous_snapshot is not None:
                                            # There is a remote snapshot that is not yet on the local host.
                                            size = ZFS.get_size(remote_dataset, previous_snapshot, snapshot, replicate_settings['endpoint'])
                                            Manager.logger.info('  {0}@{1} > {0}@{2} ({3})'.format(remote_dataset, previous_snapshot, snapshot, size))
                                            ZFS.replicate(remote_dataset, previous_snapshot, snapshot, dataset, replicate_settings.get('buffer_size', BUFFER_SIZE), replicate_settings['endpoint'], direction='pull', compression=replicate_settings['compression'])
                                            ZFS.hold(dataset, snapshot)
                                            ZFS.hold(remote_dataset, snapshot, replicate_settings['endpoint'])
                                            ZFS.release(dataset, previous_snapshot)
                                            ZFS.release(remote_dataset, previous_snapshot, replicate_settings['endpoint'])
                                            previous_snapshot = snapshot
                            elif push is True and len(local_snapshots) > 0:
                                # No common snapshot
                                if remote_dataset not in remote_snapshots:
                                    # No remote snapshot, full replication
                                    snapshot = local_snapshots[-1]
                                    size = ZFS.get_size(dataset, None, snapshot)
                                    Manager.logger.info('  {0}@         > {0}@{1} ({2})'.format(dataset, snapshot, size))
                                    ZFS.replicate(dataset, None, snapshot, remote_dataset, replicate_settings.get('buffer_size', BUFFER_SIZE), replicate_settings['endpoint'], direction='push', compression=replicate_settings['compression'])
                                    ZFS.hold(dataset, snapshot)
                                    ZFS.hold(remote_dataset, snapshot, replicate_settings['endpoint'])
                            elif push is False and remote_dataset in remote_snapshots and len(remote_snapshots[remote_dataset]) > 0:
                                # No common snapshot
                                if len(local_snapshots) == 0:
                                    # No local snapshot, full replication
                                    snapshot = remote_snapshots[remote_dataset][-1]
                                    size = ZFS.get_size(remote_dataset, None, snapshot, replicate_settings['endpoint'])
                                    Manager.logger.info('  {0}@         > {0}@{1} ({2})'.format(remote_dataset, snapshot, size))
                                    ZFS.replicate(remote_dataset, None, snapshot, dataset, replicate_settings.get('buffer_size', BUFFER_SIZE), replicate_settings['endpoint'], direction='pull', compression=replicate_settings['compression'])
                                    ZFS.hold(dataset, snapshot)
                                    ZFS.hold(remote_dataset, snapshot, replicate_settings['endpoint'])
                            Manager.logger.info('Replicating {0} complete'.format(dataset))

                        # Post execution command
                        if dataset_settings['postexec'] is not None:
                            Helper.run_command(dataset_settings['postexec'], '/')

                    # Cleaning the snapshots (cleaning is mandatory)
                    if today in local_snapshots or yesterday in local_snapshots:
                        Cleaner.clean(dataset, local_snapshots, dataset_settings['schema'], dataset_settings['recursive'])

                except Exception as ex:
                    Manager.logger.error('Exception: {0}'.format(str(ex)))

    @staticmethod
    def start():
        """
        Main entry point
        """

        Manager.init_logger()
        Manager.logger.info('Starting up')

        settings = {}
        try:
            config = ConfigParser.RawConfigParser()
            config.read('/etc/zfssnapmanager.cfg')
            for dataset in config.sections():
                settings[dataset] = {'mountpoint': config.get(dataset, 'mountpoint') if config.has_option(dataset, 'mountpoint') else None,
                                     'time': config.get(dataset, 'time'),
                                     'snapshot': config.getboolean(dataset, 'snapshot'),
                                     'recursive': config.getboolean(dataset, 'recursive') if config.has_option(dataset, 'recursive') else False,
                                     'replicate': None,
                                     'schema': config.get(dataset, 'schema'),
                                     'preexec': config.get(dataset, 'preexec') if config.has_option(dataset, 'preexec') else None,
                                     'postexec': config.get(dataset, 'postexec') if config.has_option(dataset, 'postexec') else None}
                if config.has_option(dataset, 'replicate_endpoint') and (config.has_option(dataset, 'replicate_target') or
                                                                         config.has_option(dataset, 'replicate_source')):
                    settings[dataset]['replicate'] = {'endpoint': config.get(dataset, 'replicate_endpoint'),
                                                      'target': config.get(dataset, 'replicate_target')
                                                      if config.has_option(dataset, 'replicate_target') else None,
                                                      'source': config.get(dataset, 'replicate_source')
                                                      if config.has_option(dataset, 'replicate_source') else None,
                                                      'compression': config.get(dataset, 'compression')
                                                      if config.has_option(dataset, 'compression') else None}
        except Exception as ex:
            Manager.logger.error('Exception while parsing configuration file: {0}'.format(str(ex)))

        while True:
            try:
                Manager.run(settings)
            except Exception as ex:
                Manager.logger.error('Exception: {0}'.format(str(ex)))
            time.sleep(5 * 60)


if __name__ == '__main__':
    from daemon import runner

    class Runner(object):
        """
        Runner class
        """

        def __init__(self):
            """
            Initializes Runner class
            """

            self.stdin_path = '/dev/null'
            self.stdout_path = '/dev/null'
            self.stderr_path = '/dev/null'
            self.pidfile_path = '/var/run/zfs-snap-manager.pid'
            self.pidfile_timeout = 5

        def run(self):
            """
            Starts the program (can be blocking)
            """

            _ = self
            Manager.start()

    runner_instance = Runner()
    daemon_runner = runner.DaemonRunner(runner_instance)
    daemon_runner.do_action()
