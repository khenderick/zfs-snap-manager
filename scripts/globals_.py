"""
Globals file for zsnapd
"""

from magcode.core.globals_ import settings

# settings for where files are
settings['config_dir'] = '/etc/zsnapd'
settings['log_dir'] = '/var/log'
settings['run_dir'] = '/var/run'
settings['config_file'] = settings['config_dir'] + '/' + 'process.conf'
# Zsnapd only uses one daemon
settings['pid_file'] = settings['run_dir'] + '/' + 'zsnapd.pid'
settings['log_file'] = settings['log_dir'] \
        + '/' + settings['process_name'] + '.log'
settings['panic_log'] = settings['log_dir'] \
        + '/' + settings['process_name'] + '-panic.log'

# zsnapd.py
# Dataset config file
settings['dataset_config_file'] = settings['config_dir'] \
        + '/' + 'datasets.conf'
# Print debug mark
settings['debug_mark'] = False
# Number of seconds we wait while looping in main loop...
settings['sleep_time'] = 3 # seconds
settings['debug_sleep_time'] = 20 # seconds


