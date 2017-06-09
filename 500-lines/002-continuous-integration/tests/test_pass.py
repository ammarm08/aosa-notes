import unittest

'''
Class for a passing test case.
Inherits from "unittest" lib.
Asserts true.
'''

class TestFilePass(unittest.TestCase):

  def test_pass(self):
    self.assertTrue(True)