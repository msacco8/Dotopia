import unittest
from unittest.mock import Mock
from gameClient import GameClient
import struct

PREFIX_FORMAT = "!I"

class TestGameClient(unittest.TestCase):

    def setUp(self):
        self.client = GameClient("test_user")
        self.server_address = "127.0.0.1"

    def test_connect(self):
        # Mock socket object
        mock_socket = Mock()
        self.client.sock = mock_socket

        self.client.Connect(self.server_address)

        # Check that the socket was called with the correct address and port
        mock_socket.connect.assert_called_once_with((self.server_address, 6000))

        self.client.sock.close()

    def test_update_game_state(self):
        # Mock socket object and message data
        mock_socket = Mock()
        mock_message = 'test_user|0.0:0.0:0:0~'
        prefix = struct.pack(PREFIX_FORMAT, len(mock_message))
        mock_socket.recv.return_value = prefix + mock_message.encode()
        self.client.sock = mock_socket

        prefix = struct.pack(PREFIX_FORMAT, len(mock_message))

        self.client.UpdateGameState()

        # Check that the accounts and powerUps dictionaries were updated correctly
        expected_accounts = {"test_user": {"x": "0.0", "y": "0.0", "score": "0", "size": "0"}}
        expected_powerUps = []
        self.assertEqual(self.client.accounts, expected_accounts)
        self.assertEqual(self.client.powerUps, expected_powerUps)

        self.client.sock.close()

    def test_create_user(self):
        # Mock socket object
        mock_socket = Mock()
        self.client.sock = mock_socket

        self.client.CreateUser()

        # Check that the socket was called with the correct message
        expected_message = b'0|test_user'
        mock_socket.send.assert_called_once_with(expected_message)

        self.client.sock.close()

    def test_move(self):
        # Mock socket object
        mock_socket = Mock()
        self.client.sock = mock_socket

        # Test with movement array of all False values
        movement_array = [False, False, False, False]
        self.client.Move(movement_array)

        # Check that the socket was called with the correct message
        expected_message = b'1|test_user|0000'
        mock_socket.send.assert_called_once_with(expected_message)

        self.client.sock.close()

    def test_obtain_power_up(self):
        # Mock socket object
        mock_socket = Mock()
        self.client.sock = mock_socket

        # Test with a mock powerUp dictionary
        powerUp = {"type": "test_powerUp", "x": "1.0", "y": "2.0"}
        self.client.ObtainPowerUp(powerUp)

        # Check that the socket was called with the correct message
        expected_message = b'2|test_user|test_powerUp|1.0|2.0'
        mock_socket.send.assert_called_once_with(expected_message)

        self.client.sock.close()

if __name__ == '__main__':
    unittest.main()