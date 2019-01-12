#!/usr/bin/env python

import i3ipc
import argparse
import threading
from subprocess import Popen, DEVNULL

# TODO: parse this from a config file
processes = [
    {
        'cmdline': ['terminal'],
        'workspace': 4,
        'output': 'HDMI-A-2'
    },
    {
        'cmdline': ['terminal', '--class=ranger', '-e', 'ranger'],
        'workspace': 5,
        'output': 'HDMI-A-2'
    }
]

parser = argparse.ArgumentParser(description='Start some applications with a configured layout')
parser.add_argument('-t', '--timeout', help='How long to wait for applications to start', type=int, default=5)
parser.add_argument('-v', '--verbose', help='Log actions as they are performed', action='store_true')
args = parser.parse_args()

def find_process(cmdline):
    args = cmdline.split('\0')
    for proc in processes:
        if args == proc['cmdline']:
            return proc

def on_window_new(i3, e):
    container_id = e.container.id
    process_id = e.container.pid
    with open(f'/proc/{process_id}/cmdline') as f:
        cmdline = f.read().strip(' \t\r\n\0')
    proc = find_process(cmdline)
    if proc:
        processes.remove(proc)
        if args.verbose:
            printable = ' '.join(proc['cmdline'])
            print(f'Positioning {printable}')
        if 'workspace' in proc:
            workspace = proc['workspace']
            e.container.command(f'move container to workspace {workspace}')
            if 'output' in proc:
                output = proc['output']
                i3.command(f'[workspace={workspace}] move workspace to output {output}')
    if not processes:
        i3.main_quit()

def run():
    i3 = i3ipc.Connection()
    i3.on('window::new', on_window_new)
    i3.main(args.timeout)

t = threading.Thread(target=run)
t.start()

for proc in processes:
    if args.verbose:
        printable = ' '.join(proc['cmdline'])
        print(f'Starting {printable}')
    Popen(['nohup'] + proc['cmdline'], stdout=DEVNULL, stderr=DEVNULL)

t.join()
