#!/usr/bin/python2
# Copyright (c) 2015 Kenneth Henderick <kenneth@ketronic.be>
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
Functionality to distribute the scripts to the live location and restart the service
* For testing purposes only
* Do not use without understanding the consequences
  * Running untested code might light your house on fire
  * Use with caution
  * Seriously, use with caution
"""

import os
from subprocess import check_output

if __name__ == '__main__':
    this_directory = os.path.dirname(os.path.abspath(__file__))
    print 'Copying files to local node...'
    commands = []
    for filename in ['clean.py', 'helper.py', 'manager.py', 'zfs.py']:
        commands.append('cp {0}/../scripts/{1} /usr/lib/zfs-snap-manager/{1}'.format(this_directory, filename))
        commands.append('rm -f /usr/lib/zfs-snap-manager/{0}c'.format(filename))
    commands.append('systemctl restart zfs-snap-manager')
    for command in commands:
        check_output(command, shell=True)
