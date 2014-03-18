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
from datetime import datetime

from zfs import ZFS
from clean import Cleaner


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

    @staticmethod
    def run(settings):
        """
        Executes a single run where certain volumes might or might not be snapshotted
        """

        now = datetime.now()
        today = '{0:04d}{1:02d}{2:02d}'.format(now.year, now.month, now.day)

        snapshots = ZFS.get_snapshots()
        volumes = ZFS.get_volumes()
        for volume in volumes:
            if volume in settings:
                try:
                    volume_settings = settings[volume]
                    volume_snapshots = snapshots.get(volume, [])

                    take_snapshot = volume_settings['snapshot'] is True
                    replicate = volume_settings['replicate'] is not None

                    # Decide whether we need to handle this volume
                    execute = False
                    if take_snapshot is True or replicate is True:
                        if volume_settings['time'] == 'trigger':
                            # We wait until we find a trigger file in the filesystem
                            trigger_filename = '{0}/.trigger'.format(volume_settings['mountpoint'])
                            if os.path.exists(trigger_filename):
                                Manager.logger.info('Trigger found on {0}'.format(volume))
                                os.remove(trigger_filename)
                                execute = True
                        else:
                            trigger_time = volume_settings['time'].split(':')
                            hour = int(trigger_time[0])
                            minutes = int(trigger_time[1])
                            if (now.hour > hour or (now.hour == hour and now.minute >= minutes)) and today not in volume_snapshots:
                                Manager.logger.info('Time passed for {0}'.format(volume))
                                execute = True

                    if execute is True:
                        if take_snapshot is True:
                            # Take today's snapshotzfs
                            Manager.logger.info('Taking snapshot {0}@{1}'.format(volume, today))
                            ZFS.snapshot(volume, today)
                            volume_snapshots.append(today)
                            Manager.logger.info('Taking snapshot {0}@{1} complete'.format(volume, today))

                        # Replicating, if required
                        if replicate is True:
                            Manager.logger.info('Replicating {0}'.format(volume))
                            replicate_settings = volume_settings['replicate']
                            remote_snapshots = ZFS.get_snapshots(replicate_settings['target'], replicate_settings['endpoint'])
                            last_common_snapshot = None
                            for snapshot in volume_snapshots:
                                if snapshot in remote_snapshots[replicate_settings['target']]:
                                    last_common_snapshot = snapshot
                            previous_snapshot = None
                            for snapshot in volume_snapshots:
                                if snapshot == last_common_snapshot:
                                    previous_snapshot = last_common_snapshot
                                    continue
                                if previous_snapshot is not None:
                                    # There is a snapshot on this host that is not yet on the other side.
                                    Manager.logger.info('  {0}@{1} > {0}@{2}'.format(volume, previous_snapshot, snapshot))
                                    ZFS.replicate(volume, previous_snapshot, snapshot, replicate_settings['target'], replicate_settings['endpoint'])
                                    previous_snapshot = snapshot
                                    Manager.logger.info('Replicating {0} complete'.format(volume))

                    # Cleaning the snapshots (cleaning is mandatory)
                    if today in volume_snapshots:
                        Cleaner.clean(volume, volume_snapshots, volume_settings['schema'])
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
        config = ConfigParser.ConfigParser()
        config.read('/etc/zfssnapmanager.cfg')
        for volume in config.sections():
            settings[volume] = {'mountpoint': config.get(volume, 'mountpoint'),
                                'time': config.get(volume, 'time'),
                                'snapshot': config.getboolean(volume, 'snapshot'),
                                'replicate': None,
                                'schema': config.get(volume, 'schema')}
            if config.has_option(volume, 'replicate_endpoint') and config.has_option(volume, 'replicate_target'):
                settings[volume]['replicate'] = {'endpoint': config.get(volume, 'replicate_endpoint'),
                                                 'target': config.get(volume, 'replicate_target')}

        while True:
            try:
                Manager.run(settings)
            except:
                pass
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
