#!/usr/bin/env python

import i3ipc
import argparse
import threading
from subprocess import Popen, DEVNULL
import yaml
import sys
import os

programs = []

parser = argparse.ArgumentParser(description='Start some applications with a configured layout')
parser.add_argument('-t', '--timeout', help='How long to wait for applications to start', type=int, default=5)
parser.add_argument('-v', '--verbose', help='Log actions as they are performed', action='store_true')
parser.add_argument('file',
                    help='YAML file defining applications to start (or pipe to STDIN)',
                    nargs=(1 if sys.stdin.isatty() else '?'))
args = parser.parse_args()

def find_process(cmdline):
    clargs = cmdline.split('\0')
    if args.verbose:
        printable = ' '.join(clargs)
        print(f"Matching {printable}")
    for proc in programs:
        if clargs == proc['match']:
            return proc

def on_window_new(i3, e):
    container_id = e.container.id
    process_id = e.container.pid
    if args.verbose:
        print(f'on_window_new {container_id}:{process_id}')
    with open(f'/proc/{process_id}/cmdline') as f:
        cmdline = f.read().strip(' \t\r\n\0')
    proc = find_process(cmdline)
    if proc:
        programs.remove(proc)
        if args.verbose:
            printable = ' '.join(proc['cmdline'])
            print(f'Positioning {printable}')
        if 'workspace' in proc:
            workspace = proc['workspace']
            e.container.command(f'move container to workspace {workspace}')
    if not programs:
        i3.main_quit()

i3 = i3ipc.Connection()
i3.on('window::new', on_window_new)

def launch(proc):
    if args.verbose:
        printable = ' '.join(proc['cmdline'])
        print(f'Starting {printable}')
    env = None
    if 'env' in proc:
        env = dict(os.environ)
        env.update(proc['env'])
    if args.verbose:
        printable = ' '.join(proc['match'])
        print(f'Match {printable}')
    if 'workspace' in proc:
        workspace = proc['workspace']
        i3.command(f'workspace {workspace}')
    Popen(['nohup'] + proc['cmdline'], env=env, stdout=DEVNULL, stderr=DEVNULL)

def run():
    i3.main(args.timeout)

def format_cmdline(cmdline):
    if isinstance(cmdline, list):
        return list(str(x) for x in cmdline)
    return [str(cmdline)]

def parse_config(config):
    programs = []
    for output, workspaces in config.items():
        for workspace, windows in workspaces.items():
            for title, config in windows.items():
                program = {
                    'workspace': workspace
                }
                if config:
                    program['cmdline'] = config['cmdline'] if 'cmdline' in config else title
                    program['match'] = config['match'] if 'match' in config else program['cmdline']
                    if 'env' in config:
                        program['env'] = config['env']
                else:
                    program['cmdline'] = title
                    program['match'] = title
                program['cmdline'] = format_cmdline(program['cmdline'])
                program['match'] = format_cmdline(program['match'])
                programs.append(program)
    return programs

if args.file:
    with open(args.file[0]) as f:
        config = yaml.load(f, Loader=yaml.SafeLoader)
else:
    config = yaml.load(sys.stdin, Loader=yaml.SafeLoader)
if args.verbose:
    print(f'Loaded config: {config}')

programs = parse_config(config)
if args.verbose:
    print(f'Parsed windows: {programs}')

# Start programs
t = threading.Thread(target=run)
t.start()

for program in programs:
    launch(program)

t.join()

# Move workspaces to correct outputs
for output, workspaces in config.items():
    for workspace in workspaces:
        i3.command(f'[workspace={workspace}] move workspace to output {output}')
