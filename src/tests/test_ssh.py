import unittest
from unittest.mock import patch, MagicMock, call
import paramiko
import os

# Import module to test
from src.utils.ssh import (
    add_ssh_keys, get_available_server, connect_to_proxy,
    upload_files, submit_files
)


class TestSSHUtils(unittest.TestCase):

    def test_add_ssh_keys(self):
        """Test adding SSH keys to client"""
        # Create a mock SSH client
        mock_ssh = MagicMock()

        # Call the function
        add_ssh_keys(mock_ssh)

        # Verify the correct policy was set
        mock_ssh.set_missing_host_key_policy.assert_called_once()
        # Check that the policy is an instance of AutoAddPolicy
        policy = mock_ssh.set_missing_host_key_policy.call_args[0][0]
        self.assertIsInstance(policy, paramiko.AutoAddPolicy)

    def test_get_available_server_found(self):
        """Test getting an available server when one exists"""
        # Create a mock SSH client
        mock_ssh = MagicMock()
        mock_stdout = MagicMock()
        mock_stdout.readlines.return_value = [
            "server1 down\n",
            "dl-server2 up\n",
            "server3 up\n"
        ]
        mock_ssh.exec_command.return_value = (None, mock_stdout, None)

        # Call the function
        result = get_available_server(mock_ssh)

        # Verify the result is the correct server
        self.assertEqual(result, "dl-server2")
        mock_ssh.exec_command.assert_called_once_with("rupt")

    def test_get_available_server_not_found(self):
        """Test getting an available server when none exists"""
        # Create a mock SSH client
        mock_ssh = MagicMock()
        mock_stdout = MagicMock()
        mock_stdout.readlines.return_value = [
            "server1 down\n",
            "server2 down\n",
            "server3 up\n"  # No "dl" in name
        ]
        mock_ssh.exec_command.return_value = (None, mock_stdout, None)

        # Call the function
        result = get_available_server(mock_ssh)

        # Verify no server was found
        self.assertIsNone(result)

    @patch('src.utils.ssh.paramiko.SSHClient')
    @patch('src.utils.ssh.add_ssh_keys')
    def test_connect_to_proxy_success(self, mock_add_keys, mock_ssh_client):
        """Test successful connection to proxy"""
        # Create mocks
        mock_ssh = MagicMock()
        mock_ssh_client.return_value = mock_ssh

        # Mock successful server query
        mock_stdout = MagicMock()
        mock_stdout.readlines.return_value = ["dl-server up\n"]
        mock_ssh.exec_command.return_value = (None, mock_stdout, None)

        # Call the function
        success, host, ssh = connect_to_proxy("user", "pass", "proxy.host")

        # Verify results
        self.assertTrue(success)
        self.assertEqual(host, "dl-server")
        self.assertEqual(ssh, mock_ssh)
        mock_ssh.connect.assert_called_once_with("proxy.host", username="user", password="pass")

    @patch('src.utils.ssh.paramiko.SSHClient')
    @patch('src.utils.ssh.QMessageBox')
    def test_connect_to_proxy_no_hosts(self, mock_msgbox, mock_ssh_client):
        """Test connection when no hosts are available"""
        # Create mocks
        mock_ssh = MagicMock()
        mock_ssh_client.return_value = mock_ssh

        # Mock empty server query
        mock_stdout = MagicMock()
        mock_stdout.readlines.return_value = ["server1 down\n"]
        mock_ssh.exec_command.return_value = (None, mock_stdout, None)

        # Call the function
        success, host, ssh = connect_to_proxy("user", "pass", "proxy.host")

        # Verify results
        self.assertFalse(success)
        self.assertIsNone(host)
        self.assertIsNone(ssh)
        mock_msgbox.critical.assert_called_once()

    @patch('src.utils.ssh.paramiko.SSHClient')
    def test_connect_to_proxy_auth_error(self, mock_ssh_client):
        """Test connection with authentication error"""
        # Create mocks
        mock_ssh = MagicMock()
        mock_ssh_client.return_value = mock_ssh
        mock_ssh.connect.side_effect = paramiko.AuthenticationException()

        # Call the function
        success, host, ssh = connect_to_proxy("user", "pass", "proxy.host")

        # Verify results
        self.assertFalse(success)
        self.assertIsNone(host)
        self.assertIsNone(ssh)

    @patch('src.utils.ssh.paramiko.Transport')
    @patch('src.utils.ssh.paramiko.SFTPClient')
    def test_upload_files(self, mock_sftp_client, mock_transport):
        """Test uploading files to remote server"""
        # Create mocks
        mock_ssh = MagicMock()
        mock_stdout = MagicMock()
        mock_stdout.readlines.return_value = ["/home/user\n"]
        mock_ssh.exec_command.return_value = (None, mock_stdout, None)

        mock_sftp = MagicMock()
        mock_sftp_client.from_transport.return_value = mock_sftp

        # Create test files
        test_files = [
            "/path/to/file1.txt",
            "/path/to/file2.py"
        ]

        # Create progress callback mock
        mock_callback = MagicMock()

        # Call the function
        remote_dir, remote_paths = upload_files(
            test_files, "user", "pass", mock_ssh, "host", "tempdir", mock_callback
        )

        # Verify results
        self.assertEqual(remote_dir, "/home/user/tempdir/")
        self.assertEqual(remote_paths, ["file1.txt", "file2.py"])

        # Verify SFTP usage
        mock_transport.assert_called_once_with(("host", 22))
        mock_transport.return_value.connect.assert_called_once_with(None, "user", "pass")
        mock_sftp_client.from_transport.assert_called_once()

        # Verify mkdir called
        mock_sftp.mkdir.assert_called_once_with("/home/user/tempdir/")

        # Verify SFTP puts
        self.assertEqual(mock_sftp.put.call_count, 2)
        mock_sftp.put.assert_has_calls([
            call("/path/to/file1.txt", "/home/user/tempdir/file1.txt"),
            call("/path/to/file2.py", "/home/user/tempdir/file2.py")
        ])

        # Verify progress callback
        self.assertTrue(mock_callback.call_count >= 3)  # At least start, middle, end


if __name__ == '__main__':
    unittest.main()