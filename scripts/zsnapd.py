#!/usr/bin/env python3
# Copyright (c) 2018 Matthew Grant <matt@mattgrant.net.nz>
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

import os
import os.path
import errno
import sys
import pwd
import time
import copy
import signal
import gc
import json

import psutil

# A bit of nice stuff to set up ps output as much as we can...
try:
    from setproctitle import getproctitle
    setproctitle_support = True
except ImportError:
    setproctitle_support = False

from magcode.core.process import ProcessDaemon
from magcode.core.process import SignalHandler
from magcode.core.globals_ import *
from magcode.core.utility import get_numeric_setting
from magcode.core.utility import get_boolean_setting
# import this to set up config file settings etc
import scripts.globals_
from scripts.manager import Manager
USAGE_MESSAGE = "Usage: %s [-dhv] [-c config_file]"
COMMAND_DESCRIPTION = "ZFS Snap Managment Daemon"

class ZsnapdProcess(ProcessDaemon):
    """
    Process Main Daemon class
    """
    def __init__(self, *args, **kwargs):
        super().__init__(usage_message=USAGE_MESSAGE,
            command_description=COMMAND_DESCRIPTION, *args, **kwargs)

    def main_process(self):
        """
        Main process for zfssnapd
        """

        if (settings['rpdb2_wait']):
            # a wait to attach with rpdb2...
            log_info('Waiting for rpdb2 to attach.')
            time.sleep(float(settings['rpdb2_wait']))

        log_info('program starting.')
        log_debug("The daemon_canary is: '%s'" % settings['daemon_canary'])
        # Do a nice output message to the log
        pwnam = pwd.getpwnam(settings['run_as_user'])
        if setproctitle_support:
            gpt_output = getproctitle()
        else:
            gpt_output = "no getproctitle()"
        log_debug("PID: %s process name: '%s' daemon: '%s' User: '%s' UID: %d GID %d" 
                % (os.getpid(), gpt_output, self.i_am_daemon(), pwnam.pw_name,
                    os.getuid(), os.getgid()))

        if (settings['memory_debug']):
            # Turn on memory debugging
            log_info('Turning on GC memory debugging.')
            gc.set_debug(gc.DEBUG_LEAK)

       # Create a Process object so that we can check in on ourself resource
        # wise
        self.proc_monitor = psutil.Process(pid=os.getpid())

        # Initialise  a few nice things for the loop
        debug_mark = get_boolean_setting('debug_mark') 
        sleep_time = get_numeric_setting('sleep_time', float)
        debug_sleep_time = get_numeric_setting('debug_sleep_time', float)
        sleep_time = debug_sleep_time if debug() else sleep_time

        # Initialise Manager stuff
        ds_settings = Manager.read_ds_config()

        # Process Main Loop
        while (self.check_signals()):
            
            try:
                Manager.run(ds_settings)
            except Exception as ex:
                log_error('Exception: {0}'.format(str(ex)))
            
            if debug_mark:
                log_debug("----MARK---- sleep(%s) seconds ----"
                        % sleep_time) 
            time.sleep(sleep_time)

        log_info('Exited main loop - process terminating normally.')
        sys.exit(os.EX_OK)

if (__name__ is "__main__"):
    exit_code = ZsnapdProcess(sys.argv, len(sys.argv))
    sys.exit(exit_code)



