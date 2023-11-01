# vim: expandtab smarttab ts=4

from common.configs import *

import sys
import argparse

def print_version():
    print(f'Para-Run version {VERSION}')
    sys.exit(0)

def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('cmd', nargs='*', help='Local commands. Wrap long commands with quotes(\"\").')
    parser.add_argument('-v', '--version', action='store_true', help='Show version and exit.')
    parser.add_argument('-r', '--remote-cmds', nargs=2, metavar=('REMOTE_HOSTS', 'CMD'), action='append', help='Target hosts (1-19) are allowed "," and "-", e.g. "1,3-5" is valid. Multiple -r is allowed.')
    parser.add_argument('-l', '--log-output', action='store_true', help='Store output to logs.')
    parser.add_argument('-w', '--subwin-height', type=int, help=f'The starting height of each subwindow, {DEFAULT_SUBPADS_SHOWN_HEIGHT} by default.', default=DEFAULT_SUBPADS_SHOWN_HEIGHT)
    parser.add_argument('-d', '--debug-level', type=int, help='Debug level, 0 by default.', default=0)
    args = parser.parse_args()
    if args.version:
        print_version()

    if not args.remote_cmds and len(args.cmd) == 0:
        parser.print_help()
        sys.exit(0)
    return args

def trans_cmds(args):
    cmds = list(args.cmd)
    # Remote commands specified?
    if args.remote_cmds:
        illegal_hosts = []
        def trans_remote_cmds(remote_cmd):
            hosts = []
            hosts_str, cmd = remote_cmd
            for host_str in hosts_str.split(','):
                hyphen_pos = host_str.find('-')
                if hyphen_pos == -1:
                    try:
                        hostid = int(host_str)
                        hosts.append(hostid)
                    except ValueError:
                        illegal_hosts.append(host_str)
                        continue
                else:
                    hstart = host_str[:hyphen_pos]
                    hend = host_str[hyphen_pos + 1:]
                    try:
                        hstartid = int(hstart)
                        hendid = int(hend)
                    except ValueError:
                        illegal_hosts.append(host_str)
                        continue
                    hosts += range(hstartid, hendid + 1)

            hosts = list(set(hosts)) # Unique
            for hostid in hosts:
                cmds.append('ssh n%d \"%s\"' % (hostid, cmd))

        for remote_cmd in args.remote_cmds:
            trans_remote_cmds(remote_cmd)

        if len(illegal_hosts) > 0:
            sys.stderr.write('Illegal hosts: %s\033[0m\n' % ','.join(illegal_hosts))
            sys.exit(-1)

    return cmds

def parse_cmds():
    args = parse_args()
    return args, trans_cmds(args)
