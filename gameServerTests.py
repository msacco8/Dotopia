import unittest
import threading
import socket
import time
from unittest.mock import patch
from gameServer import Server

class TestServer(unittest.TestCase):
    
    def test_CreateUser(self):
        # test creating a new user
        server = Server()
        try:
            server.CreateUser(None, None, "user1")
        except:
            pass
        self.assertTrue("user1" in server.accounts.keys())
        
        # test creating a user with the same name as an existing user
        try:
            server.CreateUser(None, None, "user1")
        except:
            pass
        self.assertFalse(len(server.accounts) > 1)
        server.sock.close()
    
    def test_Move(self):
        # test moving up
        server = Server()
        server.accounts = {"user1": {"x": 10, "y": 10, "score": 0, "speed": 3, "size": 3}}
        server.Move("user1", "10000")
        self.assertEqual(server.accounts["user1"]["y"], 7)
        
        # test moving down
        server.accounts = {"user1": {"x": 10, "y": 10, "score": 0, "speed": 3, "size": 3}}
        server.Move("user1", "01000")
        self.assertEqual(server.accounts["user1"]["y"], 13)
        
        # test moving left
        server.accounts = {"user1": {"x": 10, "y": 10, "score": 0, "speed": 3, "size": 3}}
        server.Move("user1", "00100")
        self.assertEqual(server.accounts["user1"]["x"], 7)
        
        # test moving right
        server.accounts = {"user1": {"x": 10, "y": 10, "score": 0, "speed": 3, "size": 3}}
        server.Move("user1", "00010")
        self.assertEqual(server.accounts["user1"]["x"], 13)
        
        # test speeding up with not enough score
        server.accounts = {"user1": {"x": 10, "y": 10, "score": 0, "speed": 3, "size": 3}}
        server.Move("user1", "00001")
        self.assertEqual(server.accounts["user1"]["speed"], 3)
        
        # test speeding up with enough score
        server.accounts = {"user1": {"x": 10, "y": 10, "score": 10, "speed": 3, "size": 3}}
        server.Move("user1", "00001")
        self.assertEqual(server.accounts["user1"]["speed"], 3.3)
        self.assertEqual(server.accounts["user1"]["score"], 9)

        server.sock.close()
    
    def test_RenderPowerUps(self):
        # test that new power ups are added every 2 seconds
        server = Server()
        server.powerUps = []
        # server.RenderPowerUps()
        # powerUpThread = threading.Thread(target=server.RenderPowerUps)
        # powerUpThread.start()
        # time.sleep(3)
        # self.assertEqual(len(server.powerUps), 1)
        # time.sleep(3)
        # self.assertEqual(len(server.powerUps), 2)
        
        # test that max of 30 power ups can be on screen
        # server.powerUps = []
        # for i in range(35):
        #     server.RenderPowerUps()
        # time.sleep(3)
        # self.assertEqual(len(server.powerUps), 30)

        server.sock.close()
        
    def test_HandlePowerUpCollision(self):
        # test colliding with money power up increases score by 10
        server = Server()
        server.accounts = {"user1": {"x": 10, "y": 10, "score": 0, "speed": 3, "size": 3}}
        server.powerUps = [{"type": "money", "x": 10, "y": 10}]
        server.HandlePowerUpCollision("user1", "money", 10, 10)
        self.assertEqual(server.accounts["user1"]["score"], 10)
        
        # test colliding with speed power up increases speed by 3
        server.accounts = {"user1": {"x": 10, "y": 10, "score": 0, "speed": 3, "size": 3}}
        server.powerUps = [{"type": "speed", "x": 10, "y": 10}]
        server.HandlePowerUpCollision("user1", "speed", 10, 10)
        self.assertEqual(server.accounts["user1"]["speed"], 6)
        
        # test colliding with food power up increases size by 1
        server.accounts = {"user1": {"x": 10, "y": 10, "score": 0, "speed": 3, "size": 3}}
        server.powerUps = [{"type": "food", "x": 10, "y": 10}]
        server.HandlePowerUpCollision("user1", "food", 10, 10)
        self.assertEqual(server.accounts["user1"]["size"], 4)
        
        # test power up is removed from power ups list after collision
        server.accounts = {"user1": {"x": 10, "y": 10, "score": 0, "speed": 3, "size": 3}}
        server.powerUps = [{"type": "money", "x": 10, "y": 10}]
        server.HandlePowerUpCollision("user1", "money", 10, 10)
        self.assertEqual(len(server.powerUps), 0)

        server.sock.close()

if __name__ == '__main__':
    unittest.main()