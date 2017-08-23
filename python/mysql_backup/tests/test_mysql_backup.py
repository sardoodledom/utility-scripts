import mysql_backup
import paramiko
import os
import unittest

from unittest import mock


class TestMySQLBackup(unittest.TestCase):
    """
    This unittest tests the functions for the mysql_backup.py script.
    """

    def setUp(self):
        """Setup necessary paths and fixtures"""
        self.local_backup_dir = os.path.join(os.getcwd(),
                                             'tests/local-backups')
        self.remote_backup_dir = '/tmp/backups'
        self.ssh = paramiko.SSHClient()
        self.stderr = mock.MagicMock()
        self.ssh.exec_command = mock.MagicMock(return_value=('', '',
                                                             self.stderr))

    def test_create_local_path(self):
        mysql_backup.create_local_path(self.local_backup_dir)
        self.assertTrue(os.path.exists(self.local_backup_dir))

    def test_create_remote_path(self):
        """Test remote path creation with a mock object"""

        self.stderr.channel.recv_exit_status = 0
        remote_path = mysql_backup.create_remote_path(self.ssh,
                                                      self.remote_backup_dir)
        self.assertEqual(self.remote_backup_dir, remote_path)

    def test_create_remote_path_negative(self):
        """Test that a failure returns False"""

        self.stderr.channel.recv_exit_status = 1
        remote_path = mysql_backup.create_remote_path(self.ssh,
                                                      self.remote_backup_dir)
        self.assertFalse(remote_path)

    def tearDown(self):
        """Clean up leftover resources"""

        if os.path.exists(self.local_backup_dir):
            os.removedirs(self.local_backup_dir)


if __name__ == '__main__':
    unittest.main()
