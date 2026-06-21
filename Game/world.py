import numpy as np
import random
import matplotlib.pyplot as plt
import time
from queue import Queue
from threading import Thread
from fastapi import FastAPI
import uvicorn
from pydantic import BaseModel
from typing import Optional
import datetime
from uuid import uuid4

class Action(BaseModel):
    world_id: str
    player_id : str
    action_type : str
    direction : Optional[str] = None

class SignUpRequest(BaseModel):
    name: str

class Player():
    def __init__(self, name, player_id, player_idx, energy):
        self.player_id = player_id
        self.player_idx = player_idx
        self.name = name
        self.energy = energy
        self.location = (0,0)
        self.alive = False

    def spawn(self, location):
        self.location = location
        self.alive = True

    def can_act(self):
        return self.alive and self.energy > 0

    def spend_energy(self, amount=1):
        self.energy -= amount
        if self.energy <= 0:
            self.energy = 0
            self.alive = False

    def add_energy(self, amount):
        self.energy += amount

    def set_location(self, location):
        self.location = location 

class World():
    def __init__(
            self, world_id, size=100, num_seed_walls=100, max_wall_length=10, num_energy=50, num_players=5, starting_energy=40, tick_rate_hz=10
        ):
        self.world_id = world_id

        # params
        self.size=size
        self.num_seed_walls=num_seed_walls
        self.max_wall_length=max_wall_length
        self.num_energy=num_energy
        self.num_players=num_players
        self.starting_energy=starting_energy
        self.tick_rate_hz=tick_rate_hz

        # helpers
        self.directions = {
            "up":[1,0],
            "down":[-1,0],
            "left":[0,-1],
            "right":[0,1]
        }

        # players
        self.players = {}
        self.next_player_idx = 100

        # world management
        self.running = False
        self.lobby_ready = False
        self.action_queue = Queue()
        self.map = np.zeros((size,size))
        self.game_history = []

        # misc
        self.display_gui = None

        # main loop
        Thread(target=self.update_world_loop, daemon=True).start()
        
    def _init_map(self, size=100):
        self.map = np.zeros((size,size))

    def _get_wall_direction(self, prev_direction = None, change_chance = 0.25):
            directions = [
                [0,1],    
                [0,-1],    
                [1,0],    
                [-1,0]
            ]
            if prev_direction is None:
                return random.choice(directions)

            if random.random() > change_chance:
                return prev_direction

            valid_directions = [
                dir for dir in directions
                if not(dir[0] + prev_direction[0] == 0 and dir[1] + prev_direction[1] == 0)
            ]            
            return random.choice(valid_directions)

    def _init_walls(self, num_seed_walls=10, max_wall_length=10):
        # place seed walls
        seed_walls = []
        count = 0
        tries = 0
        while count < num_seed_walls:
            if tries > 10:
                print("Error placing more walls")
                break

            x = random.randint(0,self.size-1)
            y = random.randint(0,self.size-1)
            if self.is_empty(self.map[x][y]):
                self.map[x][y] = 1
                seed_walls.append((x,y))
                count += 1
                tries = 0
            else:
                tries += 1

        # place wall growths
        # iterate over all seed walls and grow outwards
        change_chance = 0.15
        for x, y in seed_walls:
            direction = self._get_wall_direction(change_chance=change_chance)
            for _ in range(max_wall_length):
                direction = self._get_wall_direction(
                    prev_direction=direction, change_chance=change_chance
                )
                x += direction[0]
                y += direction[1]
                if x < 0 or x > self.size-1:
                    break
                elif y < 0 or y > self.size-1:
                    break
                if self.is_empty(self.map[x][y]):
                    self.map[x][y] = 1
                else:
                    break

    def _init_energy(self, num_energy=50):
        count = 0
        tries = 0 
        while count < num_energy:
            if tries > 10:
                print("Error placing more energy")
                break

            x = random.randint(0,self.size-1)
            y = random.randint(0,self.size-1)
            if self.is_empty(self.map[x][y]):
                self.map[x][y] = 2
                count += 1
                tries = 0 
            else:
                tries += 1

    def _init_players(self):
        tries = 0
        for player in self.players.values():
            if tries > 10:
                print("Error placing more players")
                break

            x = random.randint(0,self.size-1)
            y = random.randint(0,self.size-1)
            if self.is_empty(self.map[x][y]):
                player.spawn((x,y))
                self.map[x][y] = player.player_idx
                tries = 0
            else:
                tries += 1

    def _get_rgb_map(self):
        rgb_map = np.zeros((self.size,self.size,3), dtype=int)

        for i in range(self.size):
            for j in range(self.size):
                cell_value = self.map[i][j]
                if cell_value == 0: # empty
                    rgb_map[i][j][0] = 255
                    rgb_map[i][j][1] = 255
                    rgb_map[i][j][2] = 255
                elif cell_value == 1: # wall
                    rgb_map[i][j][0] = 0
                    rgb_map[i][j][1] = 0
                    rgb_map[i][j][2] = 0
                elif cell_value == 2: # energy
                    rgb_map[i][j][0] = 0
                    rgb_map[i][j][1] = 255
                    rgb_map[i][j][2] = 0
                elif cell_value >= 100: # player
                    rgb_map[i][j][0] = 0
                    rgb_map[i][j][1] = 0
                    rgb_map[i][j][2] = 255

        return rgb_map

    def add_player(self, sign_up_request):
        player_id = str(uuid4())
        self.players[player_id] = Player(
            name=sign_up_request.name,
            player_id=player_id,
            player_idx=self.next_player_idx,
            energy=self.starting_energy
        )
        self.next_player_idx += 1

        if len(self.players) > 9:
            self.lobby_ready = True
        
        return player_id

    def queue_action(self, action: Action):
        if self.running:
            self.action_queue.put(action)
            return True
        return False

    def handle_action(self, action: Action):
        if action.action_type=='move':
            self.move_player(action.player_id, action.direction)

    def move_player(self, player_id: str, direction: str):
        player = self.players[player_id]

        if not player.can_act():
            return False

        if direction not in self.directions:
            player.spend_energy(1)
            return False

        dx, dy = self.directions[direction]
        x_prev, y_prev = player.location
        x_new, y_new = x_prev + dx, y_prev + dy

        if not self.in_bounds(x_new, y_new):
            player.spend_energy(1)
            return False

        target = self.map[x_new][y_new]

        if self.is_wall(target) or self.is_player(target):
            player.spend_energy(1)
            return False

        if self.is_energy(target):
            player.add_energy(20)

        self.map[x_prev][y_prev] = 0
        self.map[x_new][y_new] = player.player_idx
        player.set_location((x_new, y_new))

        player.spend_energy(1)
        return True

    def get_player_interface(self, player_id: str):
        radius = 5
        if not self.running:
            return {
                "game_state":"not running",
                "energy": 0,
                "location": (0,0),
                "vision": np.zeros((radius*2,radius*2)).tolist()
            }

        player = self.players[player_id]

        # get square of radius around player
        x, y = player.location
        vision = self.map[x-radius:x+radius,y-radius:y+radius]
        player_interface = {
            "game_state":"running",
            "energy": player.energy,
            "location": player.location,
            "vision": vision.tolist()
        }
        return player_interface

    def end_game(self):
        # save game
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        np.save(f"games/{self.world_id}_{timestamp}", self.game_history)

        # reset world
        self.lobby_ready = False
        self.running = False
        self.game_history = []
        self.map = np.zeros((self.size,self.size))
        self.players = {}
        self.next_player_idx = 100
        self.action_queue = Queue()

    def in_bounds(self, x, y):
        return 0 <= x < self.size and 0 <= y < self.size

    def is_empty(self, cell):
        return cell == 0

    def is_wall(self, cell):
        return cell == 1

    def is_energy(self, cell):
        return cell == 2

    def is_player(self, cell):
        return cell >= 100
    
    def show_world(self):
        plt.ion()
        self.fig, self.ax = plt.subplots()
        self.img = self.ax.imshow(self._get_rgb_map())
        self.display_gui = True

    def get_world_state(self):
        return {"map": self.map.tolist()}

    def update_display(self):
        if self.display_gui:
            # update canvas
            self.img.set_data(self._get_rgb_map())
            self.fig.canvas.flush_events()
    
    def update_world_loop(self):
        while True:
            time.sleep(1/self.tick_rate_hz)
            if not self.lobby_ready:
                continue
            
            if not self.running:
                self._init_map(size=self.size)
                self._init_walls(num_seed_walls=self.num_seed_walls, max_wall_length=self.max_wall_length)
                self._init_energy(num_energy=self.num_energy)
                self._init_players()
                self.running = True
                continue 

            if all([not player.alive for player in self.players.values()]): # check if all players are dead
                self.end_game()
                continue

            # clear action queue
            players_moved = {
                key: False
                for key in self.players.keys()
            }

            while not self.action_queue.empty():
                action_batch = []
                while not self.action_queue.empty():
                    action_batch.append(self.action_queue.get())

                if action_batch:
                    for action in action_batch:
                        if not players_moved[action.player_id]: # move only once per tick
                            self.handle_action(action)
                            players_moved[action.player_id] = True

            self.game_history.append(self.map.copy())

worlds = {}
for _ in range(10):
    world_id = str(uuid4())
    worlds[world_id] = World(world_id)

app = FastAPI()

@app.get("/")
def read_root():
    return {"Hello": "World"}

@app.get("/get_worlds")
def get_worlds():
    world_info_list = {}
    for world_id, world in worlds.items():
        world_info_list[world_id] = {
            "world_id": world.world_id,
            "status": "Running" if world.running else "Stopped",
            "players": len(world.players)
        }
    return world_info_list

@app.get("/get_world_state") # have to include queyr params like so, GET /get_world_state?world_id=3959d47a-f872-49b0-a8a1-8d1529c57f73
def get_world_state(world_id: str):
    return {"world_state": worlds[world_id].get_world_state()}

@app.get("/get_player_state") # have to include query params like so, GET /get_player_state?world_id=3959d47a-f872-49b0-a8a1-8d1529c57f73&player_id=a27a54bd-52cc-4041-9aca-b04fe5ea932f
def get_player_state(world_id: str, player_id: str):
    return worlds[world_id].get_player_interface(player_id)

@app.post("/queue_action")
def queue_action(action: Action):
    action_successful = worlds[action.world_id].queue_action(action)
    return {"status":"success" if action_successful else "failure"}

@app.post("/queue_game")
def queue_game(sign_up_request: SignUpRequest):
    for world in worlds.values():
        if not world.running:
            player_id = world.add_player(sign_up_request)
            return {"status":"success", "world_id": world.world_id, "player_id": player_id}
    return {"status":"failed", "msg":"could not join world"}

if __name__=="__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
