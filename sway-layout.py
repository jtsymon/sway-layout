#!/usr/bin/env python

import i3ipc
import argparse
import threading
from subprocess import Popen, DEVNULL
import yaml
import sys
import os

processes = []

parser = argparse.ArgumentParser(description='Start some applications with a configured layout')
parser.add_argument('-t', '--timeout', help='How long to wait for applications to start', type=int, default=5)
parser.add_argument('-v', '--verbose', help='Log actions as they are performed', action='store_true')
parser.add_argument('file', help='YAML file defining applications to start (or pipe to STDIN)', nargs=(1 if sys.stdin.isatty() else '?'))
args = parser.parse_args()

def find_process(cmdline):
    clargs = cmdline.split('\0')
    if args.verbose:
        printable = ' '.join(clargs)
        print(f"Matching {printable}")
    for proc in processes:
        if clargs == proc['match']:
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

i3 = i3ipc.Connection()

def run():
    i3.on('window::new', on_window_new)
    i3.main(args.timeout)

if args.file:
    with open(args.file[0]) as f:
        processes = yaml.load(f)
else:
    processes = yaml.load(sys.stdin)
if args.verbose:
    print(f'Loaded config: {processes}')

t = threading.Thread(target=run)
t.start()

for proc in processes:
    proc['cmdline'] = list(str(x) for x in proc['cmdline'])
    if args.verbose:
        printable = ' '.join(proc['cmdline'])
        print(f'Starting {printable}')
    env = None
    if 'env' in proc:
        env = dict(os.environ)
        env.update(proc['env'])
    if not 'match' in proc:
        proc['match'] = proc['cmdline']
    if 'workspace' in proc:
        workspace = proc['workspace']
        i3.command(f'workspace {workspace}')
    Popen(['nohup'] + proc['cmdline'], env=env, stdout=DEVNULL, stderr=DEVNULL)

t.join()
