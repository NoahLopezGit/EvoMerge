import requests
import random
import time

base_url = "http://127.0.0.1:8000"
directions = ["up", "down", "left", "right"]

session = requests.Session()

for i in range(10):
    response = session.post(
        base_url + "/queue_game",
        json={"name": f"ROB{i}"},
        timeout=5,
    )
    print(response.status_code, response.json())

while True:
    for i in range(10):
        direction = random.choice(directions)

        response = session.post(
            base_url + "/queue_action",
            json={
                "world_id": 0,
                "player_id": 100 + i,
                "action_type": "move",
                "direction": direction,
            },
            timeout=5,
        )
        print(response.status_code, response.json())

    time.sleep(0.2)

    for i in range(10):
        response = session.get(
            base_url + "/get_player_state",
            params={
                "world_id": 0,
                "player_id": 100 + i,
            },
            timeout=5,
        )
        print(response.status_code, response.json())