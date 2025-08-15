import unittest
from unittest.mock import patch, MagicMock, call, mock_open
import paramiko
import os

# Import module to test
from src.utils.ssh import (
    add_ssh_keys, get_available_server, connect_to_proxy,
    upload_files, submit_files, SecureHostKeyPolicy
)


class TestSSHUtils(unittest.TestCase):

    @patch('src.utils.ssh.os.path.exists')
    @patch('src.utils.ssh.os.path.expanduser')
    def test_add_ssh_keys(self, mock_expanduser, mock_exists):
        """Test adding SSH keys to client with secure policy"""
        # Create a mock SSH client
        mock_ssh = MagicMock()
        
        # Mock the expanduser to return a test path
        mock_expanduser.return_value = '/home/user/.ssh/known_hosts'
        mock_exists.return_value = True
        
        # Call the function
        add_ssh_keys(mock_ssh)

        # Verify system and user host keys were loaded
        mock_ssh.load_system_host_keys.assert_called_once()
        mock_ssh.load_host_keys.assert_called_once_with('/home/user/.ssh/known_hosts')
        
        # Verify the correct policy was set
        mock_ssh.set_missing_host_key_policy.assert_called_once()
        # Check that the policy is an instance of SecureHostKeyPolicy
        policy = mock_ssh.set_missing_host_key_policy.call_args[0][0]
        self.assertIsInstance(policy, SecureHostKeyPolicy)

    @patch('src.utils.ssh.os.path.exists')
    @patch('src.utils.ssh.os.path.expanduser')
    def test_add_ssh_keys_no_user_known_hosts(self, mock_expanduser, mock_exists):
        """Test adding SSH keys when user known_hosts doesn't exist"""
        mock_ssh = MagicMock()
        mock_expanduser.return_value = '/home/user/.ssh/known_hosts'
        mock_exists.return_value = False
        
        add_ssh_keys(mock_ssh)
        
        # Should still load system keys and set secure policy
        mock_ssh.load_system_host_keys.assert_called_once()
        mock_ssh.load_host_keys.assert_not_called()  # File doesn't exist
        mock_ssh.set_missing_host_key_policy.assert_called_once()

    @patch('src.utils.ssh.os.path.exists')
    @patch('src.utils.ssh.os.path.expanduser')  
    def test_add_ssh_keys_load_error(self, mock_expanduser, mock_exists):
        """Test adding SSH keys with load errors"""
        mock_ssh = MagicMock()
        mock_ssh.load_system_host_keys.side_effect = Exception("System keys error")
        mock_ssh.load_host_keys.side_effect = Exception("User keys error")
        mock_expanduser.return_value = '/home/user/.ssh/known_hosts'
        mock_exists.return_value = True
        
        # Should handle errors gracefully
        add_ssh_keys(mock_ssh)
        
        # Should still set the policy even if loading fails
        mock_ssh.set_missing_host_key_policy.assert_called_once()

    def test_secure_host_key_policy_fingerprint_generation(self):
        """Test fingerprint generation in SecureHostKeyPolicy"""
        policy = SecureHostKeyPolicy()
        
        # Create a mock key
        mock_key = MagicMock()
        mock_key.get_name.return_value = "ssh-rsa"
        mock_key.get_base64.return_value = "AAAAB3NzaC1yc2EAAAADAQABAAABAQ=="
        
        # Test that the policy exists and can be instantiated
        self.assertIsInstance(policy, SecureHostKeyPolicy)

    @patch('src.utils.ssh.SecureHostKeyPolicy._console_prompt')
    @patch('src.utils.ssh.PYQT_AVAILABLE', False)
    def test_secure_host_key_policy_console_mode(self, mock_console_prompt):
        """Test SecureHostKeyPolicy in console mode"""
        policy = SecureHostKeyPolicy()
        mock_client = MagicMock()
        
        # Create a mock key with proper methods
        mock_key = MagicMock()
        mock_key.get_name.return_value = "ssh-rsa"
        mock_key.get_base64.return_value = "AAAAB3NzaC1yc2EAAAADAQABAAABAQ=="
        
        # Test missing_host_key method
        policy.missing_host_key(mock_client, "testhost", mock_key)
        
        # Verify console prompt was called with correct parameters
        mock_console_prompt.assert_called_once()
        args = mock_console_prompt.call_args[0]
        self.assertEqual(args[0], "testhost")  # hostname
        self.assertEqual(args[1], "ssh-rsa")   # key_type

    @patch('builtins.open', new_callable=mock_open)
    @patch('src.utils.ssh.os.makedirs')
    @patch('src.utils.ssh.os.path.expanduser')
    @patch('src.utils.ssh.os.path.dirname')
    def test_save_host_key(self, mock_dirname, mock_expanduser, mock_makedirs, mock_file):
        """Test saving host key to known_hosts file"""
        policy = SecureHostKeyPolicy()
        
        # Setup mocks
        mock_expanduser.return_value = '/home/user/.ssh/known_hosts'
        mock_dirname.return_value = '/home/user/.ssh'
        
        # Create a mock key
        mock_key = MagicMock()
        mock_key.get_name.return_value = "ssh-rsa"
        mock_key.get_base64.return_value = "AAAAB3NzaC1yc2EAAAADAQABAAABAQ=="
        
        # Test saving the key
        policy._save_host_key("testhost", mock_key)
        
        # Verify directory creation
        mock_makedirs.assert_called_once_with('/home/user/.ssh', mode=0o700, exist_ok=True)
        
        # Verify file was opened for append
        mock_file.assert_called_once_with('/home/user/.ssh/known_hosts', 'a')
        
        # Verify the content written to file
        handle = mock_file()
        written_content = ''.join(call.args[0] for call in handle.write.call_args_list)
        expected_content = "testhost ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQ==\n"
        self.assertEqual(written_content, expected_content)

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
        mock_ssh.connect.assert_called_once_with("proxy.host", username="user", password="pass", timeout=15, banner_timeout=10)

    @patch('src.utils.ssh.paramiko.SSHClient')
    @patch('src.utils.ssh.PYQT_AVAILABLE', False)
    def test_connect_to_proxy_no_hosts(self, mock_ssh_client):
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

    def test_upload_files(self):
        """Test uploading files to remote server using existing SSH connection"""
        # Create mocks
        mock_ssh = MagicMock()
        mock_stdout = MagicMock()
        mock_stdout.readlines.return_value = ["/home/user\n"]
        mock_ssh.exec_command.return_value = (None, mock_stdout, None)

        mock_sftp = MagicMock()
        mock_ssh.open_sftp.return_value = mock_sftp

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

        # Verify SFTP usage - should use existing SSH connection
        mock_ssh.open_sftp.assert_called_once()

        # Verify mkdir called
        mock_sftp.mkdir.assert_called_once_with("/home/user/tempdir/")

        # Verify SFTP puts
        self.assertEqual(mock_sftp.put.call_count, 2)
        mock_sftp.put.assert_has_calls([
            call("/path/to/file1.txt", "/home/user/tempdir/file1.txt"),
            call("/path/to/file2.py", "/home/user/tempdir/file2.py")
        ])

        # Verify SFTP cleanup
        mock_sftp.close.assert_called_once()

        # Verify progress callback
        self.assertTrue(mock_callback.call_count >= 3)  # At least start, middle, end


if __name__ == '__main__':
    unittest.main()