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
Provides generic functionality
"""

import re
import sys
from datetime import datetime
from subprocess import Popen, PIPE


class Toolbox(object):
    """
    Contains generic method providing generic functionality
    """

    @staticmethod
    def run_command(command, cwd):
        """
        Executes a command, returning the output. If the command fails, it raises
        """

        pattern = re.compile(r'[^\n\t@ a-zA-Z0-9_\\.:/]+')
        process = Popen(command, shell=True, cwd=cwd, stdout=PIPE, stderr=PIPE)
        out, err = process.communicate()
        return_code = process.poll()
        if return_code != 0:
            raise RuntimeError('{0} failed with return value {1} and error message {2}'.format(command, return_code, err))
        return re.sub(pattern, '', out)

    @staticmethod
    def log(value):
        """
        Logs output to stdout
        """

        now = datetime.now()
        timestamp = '{0:04d}{1:02d}{2:02d}{3:02d}{4:02d}{5:02d}'.format(now.year, now.month, now.day,
                                                                        now.hour, now.minute, now.second)
        line = '{0} - {1}\n'.format(timestamp, value)
        sys.stdout.write(line)
        with open('/var/log/zfs-snap-manager.log', 'a') as logfile:
            logfile.write(line)
