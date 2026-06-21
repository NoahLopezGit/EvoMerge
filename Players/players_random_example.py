import requests
import random
import time
from player_client import PlayerClient

session = requests.Session()

players = []
for i in range(10):
    players.append(PlayerClient(f"ROB{i}"))

while True:
    for player in players:
        direction = random.choice(player.directions)
        response = player.move(direction)
        print(response)

    time.sleep(0.2)

    for player in players:
        response = player.get_player_interface()
        print(response)
