import unittest

'''
Class for a failing test case.
Inherits from "unittest" lib.
Fails with an error message.
'''

class TestFileFail(unittest.TestCase):

  def test_fail(self):
    self.fail("This test failed.")