'''
Test Runner.

Dispatcher -> Runner "You ready?"
Runner -> Dispatcher "Yes"

Dispatcher -> Runner "heres a commit id, run the tests"
Runner -> Dispatcher "here are the results"

For now, the runner just acknowledge communication from dispatcher
'''

import argparse
import subprocess
import errno
import re
import os
import socket
import SocketServer
import time
import threading
import unittest
import helpers

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
                print 'Running tests for commit id: %s' % commit_id
                self.run_tests(commit_id, self.server.repo_folder)
                self.server.busy = False
        else:
            self.request.sendall('Invalid command')

    def run_tests(self, commit_id, repo_folder):
        output = subprocess.check_output(['./test_runner_script.sh', repo_folder, commit_id])
        print output

        test_folder = os.path.join(repo_folder, 'tests')
        suite = unittest.TestLoader().discover(test_folder)

        result_file = open('results', 'w')
        unittest.TextTestRunner(result_file).run(suite)
        result_file.close()

        result_file = open('results', 'r')
        output = result_file.read()

        helpers.communicate(self.server.dispatcher_server['host'],
                            int(self.server.dispatcher_server['port']),
                            'results:%s:%s:%s' % (commit_id, len(output), output))

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
    runner_host = args.host
    tries = 0
    if not args.port:
        runner_port = range_start
        while tries < 100:
            try:
                server = ThreadingTCPServer((runner_host, runner_port), TestHandler)
                print server
                print runner_port
                break
            except socket.error as e:
                if e.errno == errno.EADDRINUSE:
                    tries += 1
                    runner_port = runner_port + tries
                    continue
                else:
                    raise e
    else:
        runner_port = int(args.port)
        server = ThreadingTCPServer((runner_host, runner_port), TestHandler)

    server.repo_folder = args.repo
    dispatcher_host, dispatcher_port = args.dispatcher_server.split(':')
    server.dispatcher_server = { 'host': dispatcher_host, 'port': dispatcher_port } 

    # register test runner with dispatcher
    response = helpers.communicate(server.dispatcher_server['host'], int(server.dispatcher_server['port']),
                                'register:%s:%s' % (runner_host, runner_port))

    if response != 'OK':
        raise Exception('Cannot register with dispatcher')

    # every 5 seconds, ping dispatcher to make sure it is alive
    def dispatcher_checker(server):
        while not server.dead:
            time.sleep(5)
            if (time.time() - server.latest) > 10:
                try:
                    response = helpers.communicate(server.dispatcher_server['host'],
                                                   int(server.dispatcher_server['port']),
                                                   'status')
                    if response != 'OK':
                        print 'Dispatcher is no longer functional'
                        server.shutdown()
                        return
                except socket.error as e:
                    print 'Cannot communicate with dispatcher: %s' % e
                    server.shutdown()
                    return

    # each runner runs on a separate thread
    t = threading.Thread(target=dispatcher_checker, args=(server,))
    try:
        t.start()
        server.serve_forever()
    except (KeyboardInterrupt, Exception):
        server.dead = True
        t.join()

if __name__ == "__main__":
    serve() 
