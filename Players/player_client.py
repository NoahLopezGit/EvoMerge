import requests

class PlayerClient():
    def __init__(self, name):
        self.name = name
        self.base_url = "http://127.0.0.1:8000"
        self.directions = ["up", "down", "left", "right"]

        self.session = requests.Session()
        self.world_id, self.player_id = self.queue()
        print(f"Player {self.name}, queued in world: {self.world_id}")
    
    def queue(self):
        response = self.session.post(
            self.base_url + "/queue_game",
            json={"name": self.name},
            timeout=5,
        )
        response_json = response.json()
        world_id = response_json["world_id"]
        player_id = response_json["player_id"]
        return world_id, player_id

    def move(self, direction:str):
        response = self.session.post(
            self.base_url + "/queue_action",
            json={
                "world_id": self.world_id,
                "player_id": self.player_id,
                "action_type": "move",
                "direction": direction,
            },
            timeout=5,
        )
        return response.json()
    
    def get_player_interface(self):
        response = self.session.get(
            self.base_url + "/get_player_state",
            params={
                "world_id": self.world_id,
                "player_id": self.player_id,
            },
            timeout=5,
        )
        return response.json()

if __name__=="__main__":
    player = PlayerClient("ROB")
    print(player.world_id, player.player_id)