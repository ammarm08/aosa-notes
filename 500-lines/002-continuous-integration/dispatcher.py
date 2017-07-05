'''
Dispatcher.

Observer -> Dispatcher: "You alive?"
Dispatcher -> Observer: "Yes"

Observer -> Dispatcher: "this is the latest commit"

Dispatcher enqueues commits for "dispatching" to do things (in this case, tests)

For now, dispatcher will acknowledge that it received a message from the Observer
'''

import argparse
import re
import socket
import SocketServer
import time
import helpers

# extends TCPServer to handle multithreading and track some state for us
class ThreadingTCPServer(SocketServer.ThreadingMixIn, SocketServer.TCPServer):
    runners = []
    dead = False
    dispatched_commits = {}
    pending_commits = []

# request handler: pull 1 MB at a time, match the data against expected actions
class DispatcherHandler(SocketServer.BaseRequestHandler):
    command_re = re.compile(r"(\w+)(:.+)*")
    BUF_SIZE = 1024

    def handle(self):
        self.data = self.request.recv(self.BUF_SIZE).strip()
        command_groups = self.command_re.match(self.data)

        if not command_groups:
            self.request.sendall('Invalid command')
            return
        
        command = command_groups.group(1)
        if command == 'status':
            print 'in status'
            self.request.sendall('OK')
        elif command == 'dispatch':
            print 'going to dispatch'
            commit_id = command_groups.group(2)[1:]
            self.request.sendall('OK')
            print 'received and processing commit: %s' % commit_id
        else:
            self.request.sendall('Invalid command')

def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--host',
                        help = 'dispatcher host, by default uses localhost',
                        default = 'localhost',
                        action = 'store')

    parser.add_argument('--port',
                        help = 'dispatcher port, by default it uses 8888',
                        default = 8888,
                        action = 'store')

    return parser.parse_args()

def serve():
    args = parse_args()
    server = ThreadingTCPServer((args.host, int(args.port)), DispatcherHandler)
    server.serve_forever()

if __name__ == "__main__":
    serve() 





