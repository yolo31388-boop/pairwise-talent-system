import unittest

from tests import test_talent

if not issubclass(test_talent.TestTalentSystem, unittest.TestCase):
    test_talent.TestTalentSystem.assertIsNotNone = unittest.TestCase.assertIsNotNone
