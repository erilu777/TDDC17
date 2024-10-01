from lab1.liuvacuum import *
import matplotlib.pyplot as plt
import numpy as np
import random

DEBUG_OPT_DENSEWORLDMAP = False

AGENT_STATE_UNKNOWN = 0
AGENT_STATE_WALL = 1
AGENT_STATE_CLEAR = 2
AGENT_STATE_DIRT = 3
AGENT_STATE_HOME = 4

AGENT_DIRECTION_NORTH = 0
AGENT_DIRECTION_EAST = 1
AGENT_DIRECTION_SOUTH = 2
AGENT_DIRECTION_WEST = 3

MAX_ITERATIONS = 1000

def direction_to_string(cdr):
    cdr %= 4
    return  "NORTH" if cdr == AGENT_DIRECTION_NORTH else\
            "EAST"  if cdr == AGENT_DIRECTION_EAST else\
            "SOUTH" if cdr == AGENT_DIRECTION_SOUTH else\
            "WEST" #if dir == AGENT_DIRECTION_WEST

"""
Internal state of a vacuum agent
"""
class MyAgentState:

    def __init__(self, width, height):

        # Initialize perceived world state
        self.world = [[{"type": AGENT_STATE_UNKNOWN, "visit_count": 0, "recently_visited": 0, "heat": 0, "exterior": None} for _ in range(height)] for _ in range(width)]
        self.world[1][1]["type"] = AGENT_STATE_HOME

        # Agent internal state
        self.last_action = ACTION_NOP
        self.direction = AGENT_DIRECTION_EAST
        self.pos_x = 1
        self.pos_y = 1

        # Loop detection
        self.forward_counter = 0 
        

        # Metadata
        self.world_width = width
        self.world_height = height

    """
    Update perceived agent location
    """
    def update_position(self, bump):
        if not bump and self.last_action == ACTION_FORWARD:
            if self.direction == AGENT_DIRECTION_EAST:
                self.pos_x += 1
            elif self.direction == AGENT_DIRECTION_SOUTH:
                self.pos_y += 1
            elif self.direction == AGENT_DIRECTION_WEST:
                self.pos_x -= 1
            elif self.direction == AGENT_DIRECTION_NORTH:
                self.pos_y -= 1

    """
    Update perceived or inferred information about a part of the world
    """
    def update_world(self, x, y, info):
        self.world[x][y]["type"] = info

    """
    Dumps a map of the world as the agent knows it
    """
    def print_world_debug(self):
        for y in range(self.world_height):
            for x in range(self.world_width):
                if self.world[x][y]["type"] == AGENT_STATE_UNKNOWN:
                    print("?" if DEBUG_OPT_DENSEWORLDMAP else " ? ", end="")
                elif self.world[x][y]["type"] == AGENT_STATE_WALL:
                    print("#" if DEBUG_OPT_DENSEWORLDMAP else " # ", end="")
                elif self.world[x][y]["type"] == AGENT_STATE_CLEAR:
                    print("." if DEBUG_OPT_DENSEWORLDMAP else " . ", end="")
                elif self.world[x][y]["type"] == AGENT_STATE_DIRT:
                    print("D" if DEBUG_OPT_DENSEWORLDMAP else " D ", end="")
                elif self.world[x][y]["type"] == AGENT_STATE_HOME:
                    print("H" if DEBUG_OPT_DENSEWORLDMAP else " H ", end="")

            print() # Newline
        print() # Delimiter post-print
    
    def print_visit_count(self):
        for y in range(self.world_height):
            for x in range(self.world_width):
                print(f"[{self.world[x][y]['recently_visited']}]", end="")
            print()
        print()

    def print_heatmap(self):
        for y in range(self.world_height):
            for x in range(self.world_width):
                print(f"[{self.world[x][y]['heat']}]", end="")
            print()
        print()

    def print_exterior(self):
        for y in range(self.world_height):
            for x in range(self.world_width):
                if self.world[x][y]["exterior"]:
                    print("[E]", end="")
                else:
                    print("[I]", end="")
            print()
        print()

"""
Vacuum agent
"""
class MyVacuumAgent(Agent):

    def __init__(self, world_width, world_height, log):
        super().__init__(self.execute)
        self.initial_random_actions = 10
        self.iteration_counter = MAX_ITERATIONS
        self.state = MyAgentState(world_width, world_height)
        self.log = log

        # Initialize heatmap
        plt.ion()  # Turn on interactive mode 
        self.fig, self.ax = plt.subplots(figsize=(8, 6))
        self.heatmap = None 
        self.fig.canvas.draw()  
        self.heatmap_update_frequency = 1
        self.frame_counter = 0
        self.heatmap_reset = False

        self.turns_without_forward = 0
        self.max_turns_without_forward = 2

        self.following_wall = False
        self.wall_start = None
        self.has_passed_wall_start = False
        self.has_moved_forward = False
        self.turn_count = {"left": 0, "right": 0}
        self.current_wall = []
        self.closed_in_tiles = []
        self.outer_wall_tiles = []

        self.all_tiles_discovered = False
        self.following_wall_home = False

    def move_to_random_start_position(self, bump):
        action = random.uniform(0, 1)

        self.initial_random_actions -= 1
        self.state.update_position(bump)

        if action < 0.1666666:   # 1/6 chance
            self.state.direction = (self.state.direction + 3) % 4
            self.state.last_action = ACTION_TURN_LEFT
            return ACTION_TURN_LEFT
        elif action < 0.3333333: # 1/6 chance
            self.state.direction = (self.state.direction + 1) % 4
            self.state.last_action = ACTION_TURN_RIGHT
            return ACTION_TURN_RIGHT
        else:                    # 4/6 chance
            self.state.last_action = ACTION_FORWARD
            return ACTION_FORWARD

    def execute(self, percept):

        ###########################
        # DO NOT MODIFY THIS CODE #
        ###########################

        bump = percept.attributes["bump"]
        dirt = percept.attributes["dirt"]
        home = percept.attributes["home"]

        # Move agent to a randomly chosen initial position
        if self.initial_random_actions > 0:
            self.log(f"Moving to random start position, ({self.initial_random_actions} steps left).")
            return self.move_to_random_start_position(bump)

        # Finalize randomization by properly updating position (without subsequently changing it)
        elif self.initial_random_actions == 0:
            self.initial_random_actions -= 1
            self.state.update_position(bump)
            self.state.last_action = ACTION_SUCK
            self.log("Processing percepts after position randomization")
            return ACTION_SUCK


        ########################
        # START MODIFYING HERE #
        ########################

        self.log("\n\n\n\n\n--------NEW ITERATION--------")

        # Max iterations for the agent
        if self.iteration_counter < 1:
            if self.iteration_counter == 0:
                self.iteration_counter -= 1
                self.log("Iteration counter is now 0. Halting!")
                self.log(f"Performance: {self.performance}")
            self.state.print_visit_count()
            self.log(f"Performance: {self.performance}")
            return ACTION_NOP

        self.iteration_counter -= 1
        
        self.update_heat()

        if self.iteration_counter % self.heatmap_update_frequency == 0:
            self.update_heatmap()
        
        # Track position of agent
        self.state.update_position(bump)

        # Update perceived state of current tile
        if dirt:
            self.state.update_world(self.state.pos_x, self.state.pos_y, AGENT_STATE_DIRT)
        else:
            self.state.update_world(self.state.pos_x, self.state.pos_y, AGENT_STATE_CLEAR)
        
        #Increment visit count and recently visited
        self.state.world[self.state.pos_x][self.state.pos_y]["visit_count"] += 1

        self.update_recently_visited()

        # Get an xy-pair based on where the agent is facing
        left_offset = [(-1, 0), (0, -1), (1, 0), (0, 1)][self.state.direction]
        front_offset = [(0, -1), (1, 0), (0, 1), (-1, 0)][self.state.direction]
        right_offset = [(1, 0), (0, 1), (-1, 0), (0, -1)][self.state.direction]
        offsets = [left_offset, front_offset, right_offset]      

        if bump:
            # Mark the tile at the offset from the agent as a wall (since the agent bumped into it)
            self.state.update_world(self.state.pos_x + front_offset[0], self.state.pos_y + front_offset[1], AGENT_STATE_WALL)

        self.log(f"Position: x: {self.state.pos_x}, y: {self.state.pos_y}, Direction: {self.state.direction}")

        # Debug
        #self.state.print_visit_count()
        #self.state.print_world_debug()
        #self.state.print_heatmap()
        self.state.print_exterior()

        return self.make_decision(bump, dirt, home, offsets)

    def make_decision(self, bump, dirt, home, offsets):

        left_dx, left_dy = offsets[0]
        left_tile = self.state.world[self.state.pos_x + left_dx][self.state.pos_y + left_dy]

        front_dx, front_dy = offsets[1]
        front_x = self.state.pos_x + front_dx
        front_y = self.state.pos_y + front_dy
        front_tile = self.state.world[self.state.pos_x + front_dx][self.state.pos_y + front_dy]

        if not self.all_tiles_discovered:
            self.all_tiles_discovered = self.check_if_finished()

        if self.all_tiles_discovered:
            self.log(f"ALL TILES DISCOVERED!")
            self.log(f"Following wall home: {self.following_wall_home}")
            self.log(f"Tiles part of outer wall: {self.outer_wall_tiles}")
            self.log(f"Front tile: {self.state.pos_x + front_dx}, {self.state.pos_y + front_dy}, type: {front_tile['type']}")
            if home:
                self.log("ALL TILES VISITED AND AGENT HAS RETURNED HOME!\n\n")
                self.log(f"Number of iterations: {MAX_ITERATIONS - self.iteration_counter}")
                self.state.last_action = ACTION_NOP
                return ACTION_NOP
            elif self.following_wall_home:
                self.log(f"All tiles discovered and following wall home!")
                return self.follow_wall_home(bump, left_tile, front_tile)
            elif (front_x, front_y) in self.outer_wall_tiles:
                self.log(f"Found outer wall at x: {self.state.pos_x + front_dx}, y: {self.state.pos_y + front_dy}\nTURNING RIGHT!")
                self.following_wall_home = True
                return self.turn_right()

        if dirt: 
            self.log(f"DIRT! Position: x: {self.state.pos_x}, y: {self.state.pos_y}")
            self.state.last_action = ACTION_SUCK
            return ACTION_SUCK
        elif bump:
            if not self.following_wall:
                self.log(f"FOUND NEW WALL! Position: x: {self.state.pos_x}, y: {self.state.pos_y}")
                self.wall_start = (self.state.pos_x, self.state.pos_y)
            else:
                self.log(f"Found wall while already following wall! Position: x: {self.state.pos_x}, y: {self.state.pos_y}")
            self.log(f"BUMP!\n\n")
            return self.follow_wall(bump, offsets[0], offsets[1])
        
        if self.following_wall:
            self.log("Following wall! NOT BUMPED!")
            return self.follow_wall(bump, offsets[0], offsets[1])

        next_direction = self.get_best_direction(offsets)
        if next_direction == 1:
            self.log("Front tile is best -> going forward!")
            self.turns_without_forward = 0
            return self.go_forward()
        else:
            if self.turns_without_forward > self.max_turns_without_forward:
                self.log("Too many turns without going forward -> going forward!")
                self.turns_without_forward = 0
                return self.go_forward()
            if next_direction == 0:
                self.log("Left tile is best -> turning left!")
                self.turns_without_forward += 1
                return self.turn_left()
            else:
                self.log("Right tile is best -> turning right!")
                self.turns_without_forward += 1
                return self.turn_right()
        
    def follow_wall_home(self, bump, left_tile, front_tile):
        if bump or front_tile["type"] == AGENT_STATE_WALL:
            self.log(f"BUMPED INTO WALL! TURN RIGHT!")
            return self.turn_right()
        elif left_tile["type"] != AGENT_STATE_WALL and self.state.last_action != ACTION_TURN_LEFT:
            self.log(f"NOT wall to the left -> Turn left!")
            return self.turn_left()
        else:
            self.log(f"Wall to the left -> Go forward!")
            return self.go_forward()

    def follow_wall(self, bump, left_offset, front_offset):

        self.log(f"Left turn count: {self.turn_count['left']}, Right turn count: {self.turn_count['right']}")

        left_dx, left_dy = left_offset
        left_tile = self.state.world[self.state.pos_x + left_dx][self.state.pos_y + left_dy]

        front_dx, front_dy = front_offset
        front_offset = (self.state.pos_x + front_dx, self.state.pos_y + front_dy)

        self.log(f"Follows wall: {self.following_wall}")
        self.log(f"Has moved forward: {self.has_moved_forward}")
        self.log(f"Wall start: {self.wall_start}")

        if (self.state.pos_x, self.state.pos_y) == self.wall_start and self.has_moved_forward:
            self.has_passed_wall_start = True

        self.log(f"Has passed wall start: {self.has_passed_wall_start}")

        if self.outer_wall_finished_check(front_offset) or self.inner_wall_finished_check(front_offset):
            self.log("RETURNED TO WALL START, TURN RIGHT!")
            self.has_moved_forward = False
            self.following_wall = False
            self.wall_start = None
            self.turn_count["right"] = 0
            self.turn_count["left"] = 0
            self.current_wall = [] 
            self.has_passed_wall_start = False
            return self.turn_right()

        if bump:
            self.log("Bumped into wall, turn right!")
            self.following_wall = True
            self.turn_count["right"] += 1
            self.current_wall.append(front_offset)
            return self.turn_right()

        if left_tile["type"] == AGENT_STATE_WALL or self.state.last_action == ACTION_TURN_LEFT:
            self.log("Wall to the left/just moved left -> go forward!")
            self.has_moved_forward = True
            return self.go_forward()
        elif left_tile["type"] == AGENT_STATE_UNKNOWN or (left_tile["type"] != AGENT_STATE_WALL and self.state.last_action == ACTION_FORWARD):
            self.log("Just moved forward, left tile is unknown/isn't a wall -> Turn left!")
            self.turn_count["left"] += 1
            return self.turn_left()
        self.log("Turn right!")
        self.turn_count["right"] += 1
        return self.turn_right()

    def outer_wall_finished_check(self, front_offset):
        if front_offset in self.current_wall and self.has_passed_wall_start and self.turn_count["right"] > self.turn_count["left"] and (self.turn_count["right"] - self.turn_count["left"]) % 4 == 0:
            self.log(f"Tiles that are part of wall: {self.current_wall}")
            self.log("JUST FINISHED FOLLOWING OUTER WALL!")
            self.outer_wall_tiles = self.current_wall
            self.update_world_borders()          
            return True  

    def inner_wall_finished_check(self, front_offset):
        if self.has_passed_wall_start and self.has_moved_forward and self.turn_count["right"] < self.turn_count["left"]:
            self.log("JUST FINISHED FOLLOWING INNER WALL!")
            self.flood_fill_inner(self.current_wall[-1][0], self.current_wall[-1][1])
            return True
  
    def update_world_borders(self):
        self.log(f"UPDATING BORDER!")
        self.log(f"First tile in outer wall: {self.outer_wall_tiles[0]}, x: {self.outer_wall_tiles[0][0]}, y: {self.outer_wall_tiles[0][1]}")
        self.flood_fill_outer(self.outer_wall_tiles[0][0], self.outer_wall_tiles[0][1])
        for x in range(self.state.world_width):
            for y in range(self.state.world_height):
                if self.state.world[x][y]["exterior"]:
                    self.state.world[x][y]["type"] = AGENT_STATE_WALL

    def flood_fill_outer(self, x, y):
        if  x < 0 or x >= self.state.world_width or y < 0 or y >= self.state.world_height or self.state.world[x][y]["type"] == AGENT_STATE_CLEAR or self.state.world[x][y]["exterior"]:
            self.log(f"{x}, {y} is an interior tile!")
            return
        self.log(f"Flood fill at {x}, {y}!")
        self.state.world[x][y]["exterior"] = True
        self.flood_fill_outer(x + 1, y)  
        self.flood_fill_outer(x - 1, y)
        self.flood_fill_outer(x, y + 1)
        self.flood_fill_outer(x, y - 1)

    def flood_fill_inner(self, x, y):
        if self.state.world[x][y]["type"] != AGENT_STATE_WALL and self.state.world[x][y]["type"] != AGENT_STATE_UNKNOWN or (x, y) in self.closed_in_tiles:
            return
        self.log(f"Flood fill interior wall at {x}, {y}!")
        self.state.world[x][y]["type"] = AGENT_STATE_WALL
        self.closed_in_tiles.append((x, y))
        self.flood_fill_inner(x + 1, y)  
        self.flood_fill_inner(x - 1, y)
        self.flood_fill_inner(x, y + 1)
        self.flood_fill_inner(x, y - 1)

    def get_best_direction(self, offsets):
        look_ahead_distance = 5
        forward_bonus_factor = 3
        direction_points = []
        for offset in offsets:
            random_bonus_factor = random.uniform(0.9, 1.1)
            dx, dy = offset
            direction_score = 0
            tiles_checked = 0
            for distance in range(1, look_ahead_distance):
                x = self.state.pos_x + dx * distance
                y = self.state.pos_y + dy * distance
                if 0 <= x < self.state.world_width and 0 <= y < self.state.world_height:
                    tiles_checked += 1
                    direction_score += self.state.world[x][y]["heat"] / (distance)
                    if (self.state.world[x][y]["type"] == AGENT_STATE_WALL and distance == 1):
                        direction_score = float('-inf')
                        break
            if tiles_checked < 1:
                direction_score = float('-inf')
            if offset == offsets[1]:
                self.log(f"Forward score: {direction_score}")
                direction_score *= forward_bonus_factor
            direction_points.append(((direction_score / tiles_checked) + tiles_checked) * random_bonus_factor)
        self.log(f"Direction points: {direction_points}")
        return direction_points.index(max(direction_points))

    def find_unchecked_tiles(self):
        for y in range(self.state.world_height):
            for x in range(self.state.world_width):
                if self.state.world[x][y]["type"] == AGENT_STATE_UNKNOWN:
                    return self.state.world[x][y]
        return

    def turn_left(self):
        self.state.direction = (self.state.direction + 3) % 4
        self.state.last_action = ACTION_TURN_LEFT
        return ACTION_TURN_LEFT
    
    def turn_right(self):
        self.state.direction = (self.state.direction + 1) % 4
        self.state.last_action = ACTION_TURN_RIGHT
        return ACTION_TURN_RIGHT
    
    def go_forward(self):
        self.state.last_action = ACTION_FORWARD
        return ACTION_FORWARD

    def turn_random(self):
        action = random()
        if action < 0.5:
            return self.turn_left()
        else:
            return self.turn_right()

    def check_if_finished(self):
        for y in range(1, self.state.world_height - 1):
            for x in range(1, self.state.world_width - 1):
                if self.state.world[x][y]["type"] == AGENT_STATE_UNKNOWN:
                    return False
        return True

    def reset_heatmap(self):
        for y in range(self.state.world_height):
            for x in range(self.state.world_width):
                self.state.world[x][y]["heat"] = 0
                self.state.world[x][y]["visit_count"] = 0
                self.state.world[x][y]["recently_visited"] = 0

    def create_heatmap_slope(self):
        for y in range(self.state.world_height):
            for x in range(self.state.world_width):
                if self.state.world[x][y]["type"] != AGENT_STATE_WALL:
                    self.state.world[x][y]["visit_count"] += (x + y)
        self.log("Slope created!")

    def update_recently_visited(self):
        for y in range(self.state.world_height):
            for x in range(self.state.world_width):
                if self.state.pos_x == x and self.state.pos_y == y:
                    self.state.world[x][y]["recently_visited"] = 0
                else:
                    self.state.world[x][y]["recently_visited"] += 1

    def update_heat(self):
        wall_penalty_factor = -1
        unknown_bonus_factor = 5
        visit_count_penalty_factor = -2
        recently_visited_bonus_factor = 1
        outer_wall_bonus_factor = 5
        for y in range(self.state.world_height):
            for x in range(self.state.world_width):
                tile = self.state.world[x][y]
                if tile["type"] == AGENT_STATE_WALL:
                    tile["heat"] = (MAX_ITERATIONS - self.iteration_counter) * wall_penalty_factor
                else:   
                    tile["heat"] = (tile["visit_count"] * visit_count_penalty_factor + tile["recently_visited"] * recently_visited_bonus_factor) 
                    if tile["type"] == AGENT_STATE_UNKNOWN:
                        tile["heat"] += unknown_bonus_factor * (MAX_ITERATIONS - self.iteration_counter)
                if self.all_tiles_discovered:
                    if (x, y) in self.outer_wall_tiles:
                        tile["heat"] += outer_wall_bonus_factor * (MAX_ITERATIONS - self.iteration_counter)

    def update_heatmap(self):
        visit_counts = np.zeros((self.state.world_width, self.state.world_height))
        for y in range(self.state.world_height):
            for x in range(self.state.world_width):
                if self.state.world[x][y]["type"] == AGENT_STATE_WALL:
                    pass
                    visit_counts[x, y] = -1 
                else:
                    pass
                visit_counts[x, y] = self.state.world[x][y]["heat"] 

        masked_visit_counts = np.ma.masked_where(visit_counts == -1, visit_counts)

        # Calculate dynamic vmax
        current_max_heat = np.max(masked_visit_counts) 
        current_min_heat = np.min(masked_visit_counts)

        if self.heatmap is None:  # Create heatmap on first update
            # Use 'Reds' colormap for white to dark red
            self.heatmap = self.ax.imshow(
                masked_visit_counts.T, 
                cmap="Reds", 
                interpolation="nearest", 
                vmin=current_min_heat,  
                vmax=max(1, current_max_heat) 
            )
            self.cbar = self.fig.colorbar(self.heatmap, label="Visit Count")
            
        else:
            self.heatmap.set_data(masked_visit_counts.T)
            self.heatmap.set_clim(vmin=current_min_heat, vmax=max(1, current_max_heat))  # Update colorbar range
            self.cbar.update_normal(self.heatmap)  # Update colorbar

        self.ax.set_title("Agent Heatmap")
        self.ax.set_xlabel("X Position")
        self.ax.set_ylabel("Y Position")

        self.ax.grid(True, which='major', color='black', linestyle='-', linewidth=1)
        self.ax.set_xticks(np.arange(-0.5, self.state.world_width, 1))  # Align with tile edges
        self.ax.set_yticks(np.arange(-0.5, self.state.world_height, 1)) # Align with tile edges 

        # Remove tick labels
        self.ax.set_xticklabels([])
        self.ax.set_yticklabels([])

        self.fig.canvas.draw()
        self.fig.canvas.flush_events()


    