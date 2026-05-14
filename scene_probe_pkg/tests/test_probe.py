"""Tests for the scene probe module."""

import unittest
from scene_probe import SceneProbe

class TestSceneProbe(unittest.TestCase):
    """Test cases for SceneProbe class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.probe = SceneProbe()
    
    def test_initialization(self):
        """Test that SceneProbe initializes correctly."""
        self.assertIsNotNone(self.probe)

if __name__ == "__main__":
    unittest.main()
