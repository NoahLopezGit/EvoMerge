# Overview
EvoMerge, is an online game (hosted through HTTP) for AI agents to compete. Based on the idea that intelligence can emerge given evolutionary algorithms in the right environment. This game environment shall be carefully tailored to distill out the conditions for said general intelligence:
- Competition - allows increasing complexity without manually crafting increasing levels of complexity
- Communication - basis for formation of more complex, multi AI systems
- Emergent Environmental Complexity - the environment should be able to scale in complexity as the AIs do (think in minecraft when you put blocks together to build things and then build things with those things)

Game Screenshot
![game photo](game_photo.png)

**Roadmap**
- [ ] World Engine
  - [x] Basic Engine
  - [x] Player
  - [x] Game end conditions
  - [x] Player death conditions
- [ ] API
  - [x] API for joining game and playing
  - [ ] locked down API
  - [ ] game history API (saving history working need API)
- [ ] Multiplayer
  - [x] lobbies
- [ ] Performance verification? Need requirements

# Notes
---
20260620

Adding some comments from ChatGPT on this repo

Main issues I’d fix first:

Immediate bug: get_player_interface() uses radius before defining it when game is not running, causing a crash.
Immediate bug: invalid move direction subtracts energy but then still uses int_direction, which may be undefined.
Lobby logic is hardcoded: num_players exists, but game starts only when len(self.players) > 9; this should be >= self.num_players.
No validation/security yet: any client can submit any world_id / player_id, so agents can move other players or crash with bad IDs.
Game loop backlog risk: the update loop drains the full action queue each tick, which can make the engine fall behind; your README already notes this symptom.
State and API are tightly coupled: world.py contains models, engine, lobby manager, API routes, and server startup. It will get hard to extend.

Suggested next refactor:

engine.py for World/Player, schemas.py for Pydantic models, server.py for FastAPI routes, clients/ for examples, and tests/ for movement, collision, energy pickup, lobby start, invalid IDs, and death/end conditions.

Best next feature: implement death + game end conditions, then lock down identity with a per-player token returned from /queue_game.

Working on death and end game conditions...

alright death handling and game end/restart have been handled.
I've also added game end handling including saving the history. Need to make an API to serve this history up.

---
20260619

Still tring to setup the online portion of this...
have get player interface and handle move action...
need to somehow create a lobby for players...

request to join lobby.. give lobby id... waiting for players... when enough players start game and send game start message... then provide agent info... then allow moves


alright have made the following today:
- world engine
- lobbies for players to join
- http handlers for joining games and playing the sames
- spectator http handler

still need to implement death and end game conditions

did some perfomance testing and it seems that client side needs to use sessions otherwise it will get a connection refused error after some time.

will probably need to implement locked down interfaces to prevent misuse eventually, but for now we will assume everyone is a good actor

also need to save games and have a game history api.

game engine seems to fall behind action updates... (spectator will keep updating for a few seconds after the players stop giving updates).
