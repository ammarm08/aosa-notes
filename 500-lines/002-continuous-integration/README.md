# Continuous Integration System

A continuous integration system that, upon a new commit for a given repo, runs whole test suite.

In this example, we assume the test suite exists in `<repo>/tests` and consists of Python unit tests.

Following along here: http://aosabook.org/en/500L/a-continuous-integration-system.html

## Usage

In one terminal, start the dispatcher

```bash
$ python dispatcher.py
```

In another terminal, start the test runner

```bash
$ python test_runner.py <path/to/cloned/repo>
```

Finally, in a third terminal, start the observer

```bash
$ python observer.py --dispatcher-server=localhost:8888 <path/to/cloned/repo>
```

## Architecture

- p1: An observer listens to a clone of the repo you're watching for new commits
- p2: A test runner runs tests as recent as a given commit id
- p3: A dispatcher manages commits to run tests for and test runners that can run them

Observer:

- Watches a clone of the master repo for new commit IDs
- Sends commit IDs to dispatcher when new commit IDs are found
- Bails out if dispatcher is unresponsive (periodically pings it)

Test Runner:

- Receives commit IDs to run tests for
- Runs unit tests
- Sends test results to dispatcher
- Bails out if dispatcher is unresponsive (periodically pings it on a separate thread)

Dispatcher:

- Receives commit IDs from observer
- Manages a dictionary of commits that have been dispatched to a runner
- Manages an array of commits that are pending (didn't get dispatched or their runner died)
- Receives port registration from test runner
- Receives test results from test runner
- Manages array of runners read to run tests
- Periodically attempts to re-dispatch commits that are in the pending list (separate thread)
- Periodically checks responsiveness of each runner and cleans up commit and runner lists as necessary (separate thread)