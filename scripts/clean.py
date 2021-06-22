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
Provides functionality for cleaning up old ZFS snapshots
"""

import re
from datetime import datetime

from zfs import ZFS


class Cleaner(object):
    """
    Cleaner class, containing all methods for cleaning up ZFS snapshots
    """

    logger = None  # The manager will fill this object

    @staticmethod
    def clean(dataset, snapshots, schema, recursive):
        today = datetime.now()

        # Parsing schema
        match = re.match('^(?P<days>[0-9]+)d(?P<weeks>[0-9]+)w(?P<months>[0-9]+)m(?P<years>[0-9]+)y$', schema)
        if not match:
            Cleaner.logger.info('Got invalid schema for dataset {0}: {1}'.format(dataset, schema))
            return
        matchinfo = match.groupdict()
        settings = {}
        for key in matchinfo.keys():
            settings[key] = int(matchinfo[key])

        # Loading snapshots
        snapshot_dict = []
        held_snapshots = []
        for snapshot in snapshots:
            if re.match('^(\d{4})(1[0-2]|0[1-9])(0[1-9]|[1-2]\d|3[0-1])$', snapshot) is not None:
                if ZFS.is_held(dataset, snapshot):
                    held_snapshots.append(snapshot)
                    continue
                snapshot_dict.append({'name': snapshot,
                                      'time': datetime.strptime(snapshot, '%Y%m%d'),
                                      'age': (today - datetime.strptime(snapshot, '%Y%m%d')).days})

        buckets = {}
        counter = -1
        for i in range(settings['days']):
            counter += 1
            buckets[counter] = []
        for i in range(settings['weeks']):
            counter += 7
            buckets[counter] = []
        for i in range(settings['months']):
            counter += 28
            buckets[counter] = []
        for i in range(settings['years']):
            counter += (28 * 12)
            buckets[counter] = []

        will_delete = False

        end_of_life_snapshots = []
        for snapshot in snapshot_dict:
            possible_keys = []
            for key in buckets:
                if snapshot['age'] <= key:
                    possible_keys.append(key)
            if possible_keys:
                buckets[min(possible_keys)].append(snapshot)
            else:
                will_delete = True
                end_of_life_snapshots.append(snapshot)

        to_delete = {}
        to_keep = {}
        for key in buckets:
            oldest = None
            if len(buckets[key]) == 1:
                oldest = buckets[key][0]
            else:
                for snapshot in buckets[key]:
                    if oldest is None:
                        oldest = snapshot
                    elif snapshot['age'] > oldest['age']:
                        oldest = snapshot
                    else:
                        will_delete = True
                        to_delete[key] = to_delete.get(key, []) + [snapshot]
            to_keep[key] = oldest
            to_delete[key] = to_delete.get(key, [])

        if will_delete is True:
            Cleaner.logger.info('Cleaning {0}'.format(dataset))
            for snapshot in held_snapshots:
                Cleaner.logger.info('  Skipping held {0}@{1}'.format(dataset, snapshot))

        keys = to_delete.keys()
        keys.sort()
        for key in keys:
            for snapshot in to_delete[key]:
                Cleaner.logger.info('  Destroying {0}@{1}'.format(dataset, snapshot['name']))
                ZFS.destroy(dataset, snapshot['name'], recursive)
        for snapshot in end_of_life_snapshots:
            Cleaner.logger.info('  Destroying {0}@{1}'.format(dataset, snapshot['name']))
            ZFS.destroy(dataset, snapshot['name'], recursive)

        if will_delete is True:
            Cleaner.logger.info('Cleaning {0} complete'.format(dataset))
