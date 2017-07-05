'''
Observer.

Checks for new commits to master.
Logs each new commit out to console.

TBD: dispatch + test-runner + reporter
'''

import argparse
import os
# import re
import socket
# import SocketServer
import subprocess
# import sys
import time

# import helpers

def parse_args():
    parser = argparse.ArgumentParser()

    parser.add_argument('--dispatcher-server', 
                        help = 'dispatcher host:port, defaults to localhost:8888',
                        default = 'localhost:8888',
                        action = 'store')

    parser.add_argument('repo', 
                        metavar = 'REPO', 
                        type = str,
                        help = 'path to the repo this will observe')

    return parser.parse_args()

def poll():
    args = parse_args()
    dispatcher_host, dispatcher_port = args.dispatcher_server.split(':')

    while True:
        try:
            subprocess.check_output(['./update_repo.sh', args.repo])
        except subprocess.CalledProcessError as e:
            raise Exception('Could not update and check repo. Reason: %s' % e.output)

        if os.path.isfile('.commit_id'):
            with open('.commit_id', 'r') as f:
                commit = f.readline()
            print 'Current commit: %s' % commit
            
            # try:
            #     response = helpers.communicate(dispatcher_host, int(dispatcher_port), 'status')
            # except socket.error as e:
            #     raise Exception('Could not communicate with dispatcher server %s' % e)

            # if response == 'OK':
            #     commit = ''
            #     with open('.commit_id', 'r') as f:
            #         commit = f.readline()

            #     response = helpers.communicate(dispatcher_host, int(dispatcher_port), 'dispatch:%s' % commit)
            #     if response != "OK":
            #         raise Exception("Could not dispatch the test: %s" % response)

            #     print "dispatched!"
            # else:
            #     raise Exception("Could not dispatch the test: %s" % response)
        
        time.sleep(5)

if __name__ == "__main__":
    poll()
