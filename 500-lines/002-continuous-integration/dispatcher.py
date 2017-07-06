'''
Dispatcher.

Dispatcher enqueues commits for "dispatching" to do things (in this case, tests)
and dispatches these commits to active "test runners"
'''

import argparse
import re
import socket
import SocketServer
import time
import helpers
import threading
import os

# every 2 seconds, try and run tests on each runner
def dispatch_tests(server, commit_id):
    while True:
        print 'trying to dispatch runners'
        for runner in server.runners:
            response = helpers.communicate(runner['host'], int(runner['port']), 'runtest:%s' % commit_id)
            if response == 'OK':
                print 'adding id %s' % commit_id
                server.dispatched_commits[commit_id] = runner
                if commit_id in server.pending_commits:
                    server.pending_commits.remove(commit_id)
                return
        time.sleep(2)

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
        elif command == 'register':
            print 'register'
            address = command_groups.group(2)
            host, port = re.findall(r":(\w*)", address)
            runner = { 'host': host, 'port': port }
            self.server.runners.append(runner)
            self.request.sendall('OK')
        elif command == 'dispatch':
            print 'going to dispatch'
            commit_id = command_groups.group(2)[1:]
            if not self.server.runners:
                self.request.sendall("No runners are registered")
            else:
                self.request.sendall('OK')
                print 'received and processing commit: %s' % commit_id
                dispatch_tests(self.server, commit_id)
        elif command == 'results':
            print 'getting results'
            results = command_groups.group(2)[1:]
            results = results.split(':')
            commit_id = results[0]

            len_msg = int(results[1])
            remaining = self.BUF_SIZE - (len(command) + len(commit_id) + len(results[1]) + len(':::'))
            if len_msg > remaining:
                self.data += self.request.recv(len_msg - remaining).strip()

            del self.server.dispatched_commits[commit_id]
            if not os.path.exists('test_results'):
                os.makedirs('test_results')
            with open('test_results/%s' % commit_id, 'w') as f:
                data = self.data.split(':')[3:]
                data = '\n'.join(data)
                f.write(data)
            self.request.sendall('OK')
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

    def runner_checker(server):
        # cleanup a runner -- move any commits dispatched to runner to pending commits list
        def manage_commit_lists(runner):
            for commit, assigned_runner in server.dispatched_commits.iteritems():
                if assigned_runner == runner:
                    del server.dispatched_commits[commit]
                    server.pending_commits.append(commit)
                    break
            server.runners.remove(runner)

        # ping each runner
        while not server.dead:
            time.sleep(1)
            for runner in server.runners:
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                try:
                    response = helpers.communicate(runner['host'], int(runner['port']), 'ping')
                    if response != 'pong':
                        print 'removing runner %s' % runner
                        manage_commit_lists(runner)
                except socket.error as e:
                    manage_commit_lists(runner)

    # redispatch tests that failed
    def redistribute(server):
        while not server.dead:
            for commit in server.pending_commits:
                print 'running redistribute'
                print server.pending_commits
                dispatch_tests(server, commit)
                time.sleep(5)

    # run heartbeat, redistributor, and server on separate threads
    runner_heartbeat = threading.Thread(target=runner_checker, args=(server,))
    redistributor = threading.Thread(target=redistribute, args=(server,))
    try:
        runner_heartbeat.start()
        redistributor.start()
        server.serve_forever()
    except (KeyboardInterrupt, Exception):
        server.dead = True
        runner_heartbeat.join()
        redistributor.join()

if __name__ == "__main__":
    serve() 





