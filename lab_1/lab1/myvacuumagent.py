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
        self.world = [[{"type": AGENT_STATE_UNKNOWN, "visit_count": 0, "recently_visited": 0, "heat": 0} for _ in range(height)] for _ in range(width)]
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
        self.max_turns_without_forward = 5

        self.following_wall = False

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

        self.log("--------NEW ITERATION--------")

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
        """
        left_tile = self.state.world[self.state.pos_x + left_offset[0]][self.state.pos_y + left_offset[1]]
        front_tile = self.state.world[self.state.pos_x + front_offset[0]][self.state.pos_y + front_offset[1]]
        right_tile = self.state.world[self.state.pos_x + right_offset[0]][self.state.pos_y + right_offset[1]]
        """
        offsets = [left_offset, front_offset, right_offset]

        if bump:
            # Mark the tile at the offset from the agent as a wall (since the agent bumped into it)
            self.state.update_world(self.state.pos_x + front_offset[0], self.state.pos_y + front_offset[1], AGENT_STATE_WALL)

        self.log(f"Position: x: {self.state.pos_x}, y: {self.state.pos_y}, Direction: {self.state.direction}")

        # Debug
        #self.state.print_visit_count()
        #self.state.print_world_debug()
        self.state.print_heatmap()

        return self.make_decision(bump, dirt, home, offsets)

    def make_decision(self, bump, dirt, home, offsets):

        if bump:
            self.log(f"BUMP!\n\n")

        # Decide action
        if self.check_if_finished():
            self.log("ALL TILES VISITED!\n\n\n\n")
            if home:
                self.log("ALL TILES VISITED AND AGENT HAS RETURNED HOME!\n\n")
                self.log(f"Number of iterations: {MAX_ITERATIONS - self.iteration_counter}")
                self.state.last_action = ACTION_NOP
                return ACTION_NOP
            else:
                if not self.heatmap_reset:
                    self.heatmap_reset = True
                    self.reset_heatmap()
                self.create_heatmap_slope()

        if dirt:
            self.log("DIRT -> choosing SUCK action!")
            self.state.last_action = ACTION_SUCK
            return ACTION_SUCK
        else:
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


    def get_best_direction(self, offsets):
        look_ahead_distance = 5
        forward_bias_factor = 2
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
                direction_score *= forward_bias_factor
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
        self.log("ALL TILES VISITED!\n\n\n\n")
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
                    self.state.world[x][y]["visit_count"] += (x + y)**2
        self.log("Slope created!")

    def update_recently_visited(self):
        for y in range(self.state.world_height):
            for x in range(self.state.world_width):
                if self.state.pos_x == x and self.state.pos_y == y:
                    self.state.world[x][y]["recently_visited"] = 0
                else:
                    self.state.world[x][y]["recently_visited"] += 1

    def update_heat(self):
        wall_penalty_factor = -3
        unknown_bonus_factor = 5
        visit_count_penalty_factor = -2
        recently_visited_bonus_factor = 1
        for y in range(self.state.world_height):
            for x in range(self.state.world_width):
                tile = self.state.world[x][y]
                if tile["type"] == AGENT_STATE_WALL:
                    tile["heat"] = (MAX_ITERATIONS - self.iteration_counter) * wall_penalty_factor
                else:   
                    tile["heat"] = (tile["visit_count"] * visit_count_penalty_factor + tile["recently_visited"] * recently_visited_bonus_factor) 
                    if tile["type"] == AGENT_STATE_UNKNOWN:
                        tile["heat"] += unknown_bonus_factor * (MAX_ITERATIONS - self.iteration_counter)

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
                vmin=current_min_heat,  # White starts at 0 visits
                vmax=max(1, current_max_heat) # Adjust vmax as needed
            )
            self.cbar = self.fig.colorbar(self.heatmap, label="Visit Count")
            
            # Set wall color to blue
            #self.heatmap.cmap.set_bad('blue') 
        else:
            self.heatmap.set_data(masked_visit_counts.T)
            self.heatmap.set_clim(vmin=current_min_heat, vmax=max(1, current_max_heat))  # Update colorbar range
            self.cbar.update_normal(self.heatmap)  # Update colorbar

        self.ax.set_title("Heatmap of Agent's Visits")
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


    