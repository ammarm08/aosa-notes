'''
Test Runner.

Dispatcher -> Runner "You ready?"
Runner -> Dispatcher "Yes"

Dispatcher -> Runner "heres a commit id, run the tests"
Runner -> Dispatcher "here are the results"

For now, the runner just acknowledge communication from dispatcher
'''

import argparse
import errno
import re
import socket
import SocketServer
import time

# custom TCP class with some state 
class ThreadingTCPServer(SocketServer.ThreadingMixIn, SocketServer.TCPServer):
    dispatcher = None
    latest = None
    busy = False
    dead = False

# request handler that accepts ping and runtest commands. responds with pong and busy/OK
class TestHandler(SocketServer.BaseRequestHandler):
    command_re = re.compile(r"(\w+)(:.+)*")

    def handle(self):
        self.data = self.request.recv(1024).strip()
        command_groups = self.command_re.match(self.data)
        command = command_groups.group(1)

        if not command:
            self.request.sendall('Invalid command')
            return

        if command == 'ping':
            print 'pinged'
            self.server.latest = time.time()
            self.request.sendall('pong')
        elif command == 'runtest':
            print 'got runtest command: am I busy? %s' % self.server.busy

            if self.server.busy:
                self.request.sendall('BUSY')
            else:
                self.request.sendall('OK')
                print 'running tests'

                commit_id = command_groups.group(2)[1:]

                self.server.busy = True
                print 'TBD test runner for commit id: %s' % commit_id
                self.server.busy = False
        else:
            self.request.sendall('Invalid command')

def parse_args(range_start):
    parser = argparse.ArgumentParser()
    parser.add_argument('--host',
                        help = 'runner host, by default uses localhost',
                        default = 'localhost',
                        action = 'store')
    parser.add_argument('--port',
                        help = 'runner port, by default it uses values >= %s' % range_start,
                        action = 'store')
    parser.add_argument('--dispatcher-server',
                        help = 'dispatcher host:port, by default uses localhost:8888',
                        default = 'localhost:8888',
                        action = 'store')
    parser.add_argument('repo', metavar='REPO', type=str,
                        help = 'path to repo this will observe')

    return parser.parse_args()

# scans a range of ports and selects an unused one to listen on
def serve():
    range_start = 8900
    args = parse_args(range_start)

    runner_port = None
    tries = 0
    if not args.port:
        runner_port = range_start
        while tries < 100:
            try:
                server = ThreadingTCPServer((args.host, runner_port), TestHandler)
                print server
                print runner_port
                break
            except socket.error as e:
                if e.errno == errno.EADDRINUSE:
                    tries += 1
                    runner_port = runer_port + tries
                    continue
                else:
                    raise e
    else:
        server = ThreadingTCPServer((args.host, int(args.port)), TestHandler)

    server.serve_forever()

if __name__ == "__main__":
    serve() 
