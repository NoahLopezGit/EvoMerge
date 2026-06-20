import requests

base_url = "http://127.0.0.1:8000"

for i in range(10):
    response = requests.post(
        base_url + "/queue_game",
        json={
            "name":f"ROB{i}"
        }
    )
    print(
        response.status_code,
        response.json()
    )

    input("Enter to continue")

while True:
    response = requests.post(
        base_url + "/queue_action",
        json={
            "world_id":0,
            "player_id":100,
            "action_type":"move",
            "direction":"up"
        }
    )
    print(
        response.status_code,
        response.json()
    )

    response = requests.get(
        base_url + "/get_player_state?world_id=0&player_id=100"
    )
    print(
        response.status_code,
        response.json()
    )
    input("Enter to continue")