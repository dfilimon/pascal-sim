
import pygame
import numpy as np
import itertools
import sys
import networkx as nx
import collections
import math
from pygame import gfxdraw
import random

# Game constants
BOARD_BROWN = (199, 105, 42)
BOARD_WIDTH = 1000
BOARD_BORDER = 75
STONE_RADIUS = 22
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
TURN_POS = (BOARD_BORDER, 20)
SCORE_POS = (BOARD_BORDER, BOARD_WIDTH - BOARD_BORDER + 30)
DOT_RADIUS = 4
NUM_FIG = 4
START_LIVES = 10


def make_grid(size):
    """Return list of (start_point, end_point pairs) defining gridlines
    Args:
        size (int): size of grid
    Returns:
        Tuple[List[Tuple[float, float]]]: start and end points for gridlines
    """
    start_points, end_points = [], []

    # vertical start points (constant y)
    xs = np.linspace(BOARD_BORDER, BOARD_WIDTH - BOARD_BORDER, size + 1)
    ys = np.full((size + 1), BOARD_BORDER)
    start_points += list(zip(xs, ys))

    # horizontal start points (constant x)
    xs = np.full((size + 1), BOARD_BORDER)
    ys = np.linspace(BOARD_BORDER, BOARD_WIDTH - BOARD_BORDER, size + 1)
    start_points += list(zip(xs, ys))

    # vertical end points (constant y)
    xs = np.linspace(BOARD_BORDER, BOARD_WIDTH - BOARD_BORDER, size + 1)
    ys = np.full((size + 1), BOARD_WIDTH - BOARD_BORDER)
    end_points += list(zip(xs, ys))

    # horizontal end points (constant x)
    xs = np.full((size + 1), BOARD_WIDTH - BOARD_BORDER)
    ys = np.linspace(BOARD_BORDER, BOARD_WIDTH - BOARD_BORDER, size + 1)
    end_points += list(zip(xs, ys))

    return (start_points, end_points)


def xy_to_colrow(x, y, size):
    """Convert x,y coordinates to column and row number
    Args:
        x (float): x position
        y (float): y position
        size (int): size of grid
    Returns:
        Tuple[int, int]: column and row numbers of intersection
    """
    inc = (BOARD_WIDTH - 2 * BOARD_BORDER) / (size)
    x_dist = x - BOARD_BORDER
    y_dist = y - BOARD_BORDER
    col = int(math.floor(x_dist / inc))
    row = int(math.floor(y_dist / inc))

    print(inc, x_dist, y_dist, col, row)
    
    return row, col


def colrow_to_xy(col, row, size):
    """Convert column and row numbers to x,y coordinates
    Args:
        col (int): column number (horizontal position)
        row (int): row number (vertical position)
        size (int): size of grid
    Returns:
        Tuple[float, float]: x,y coordinates of intersection
    """
    inc = (BOARD_WIDTH - 2 * BOARD_BORDER) / (size)
    x = int(BOARD_BORDER + col * inc + inc/2)
    y = int(BOARD_BORDER + row * inc + inc/2)
    return y, x


def is_valid_move(col, row, board):
    """Check if placing a stone at (col, row) is valid on board
    Args:
        col (int): column number
        row (int): row number
        board (object): board grid (size * size matrix)
    Returns:
        boolean: True if move is valid, False otherewise
    """
    if col < 0 or col >= board.shape[0]:
        return False
    if row < 0 or row >= board.shape[0]:
        return False
    return True

class Figure:
    def __init__(self, screen, id, lives, col, row):
        self.screen = screen
        self.id = id
        self.lives = lives
        self.font = pygame.font.SysFont("arial", 15)
        self.col = col
        self.row = row

    def draw(self, x, y):
        color = WHITE
        gfxdraw.aacircle(self.screen, x, y, STONE_RADIUS, color)
        gfxdraw.filled_circle(self.screen, x, y, STONE_RADIUS, color)
        txt = '#' + str(self.id) + ' ' + str(self.lives)
        self.screen.blit(self.font.render(txt, True, BLACK), (x - 10, y - 10))

    def set_pos(self, col, row):
        self.col = col
        self.row = row

    def __str__(self):
        print(self.id, self.lives, self.col, self.row)
        return ('#' + str(self.id) + ' Leben: ' + str(self.lives) +
            ' Position: (' + str(self.row + 1) + ',' + str(self.col + 1) + ')')

class Game:
    def __init__(self, size):
        self.board = np.zeros((size, size))
        self.size = size
        self.black_turn = True
        self.block_mode = False
        self.prisoners = collections.defaultdict(int)
        self.start_points, self.end_points = make_grid(self.size)
        self.figures = []
        self.zielfeld = None
        self.floating_fig = 0
        self.simulate_mode = False
        self.graph = nx.grid_graph(dim=[size, size])
        print(self.start_points)
        print(self.end_points)

    def init_pygame(self):
        pygame.init()
        screen = pygame.display.set_mode((BOARD_WIDTH, BOARD_WIDTH))
        self.screen = screen
        self.font = pygame.font.SysFont("arial", 30)

    def clear_screen(self):

        # fill board and add gridlines
        self.screen.fill(BOARD_BROWN)
        for start_point, end_point in zip(self.start_points, self.end_points):
            pygame.draw.line(self.screen, BLACK, start_point, end_point)

        pygame.display.flip()

    def pass_move(self):
        self.black_turn = not self.black_turn
        self.draw()

    def block(self):
        self.block_mode = not self.block_mode
        self.draw()

    def ziel(self):
        if self.zielfeld is not None:
            return
        x, y = pygame.mouse.get_pos()
        col, row = xy_to_colrow(x, y, self.size)
        self.zielfeld = (col, row)
        self.board[col, row] = -2
        print(self.zielfeld)
        self.draw()

    def handle_click(self):
        if self.simulate_mode:
            return

        # get board position
        x, y = pygame.mouse.get_pos()
        col, row = xy_to_colrow(x, y, self.size)
        print(self.board)
        print(x, y, col, row)
        if not is_valid_move(col, row, self.board):
            return

        # update board array
        if self.block_mode:
            print(self.board[col, row])
            if self.board[col, row] == 0:
                self.board[col, row] = -1
            elif self.board[col, row] == -1:
                self.board[col, row] = 0
            print(self.board[col, row])
        else:                        
            print('Now:', self.board[col, row], 'floating ', self.floating_fig)
            if self.board[col, row] > 0 and self.floating_fig == 0:
                self.floating_fig = self.board[col, row]
                self.board[col, row] = 0
            elif self.board[col, row] == 0 and self.floating_fig == 0:
                if len(self.figures) >= NUM_FIG:
                    return
                f = Figure(self.screen, len(self.figures) + 1, START_LIVES, col, row)
                self.figures.append(f)
                self.board[col, row] = f.id
            elif self.floating_fig > 0:
                self.board[col, row] = self.floating_fig
                self.floating_fig = 0
                self.figures[self.floating_fig - 1].set_pos(col, row)
            print('After:', self.board[col, row], 'floating ', self.floating_fig)
            
        print(self.board)


        # get stone groups for black and white
        self_color = "black" if self.black_turn else "white"
        other_color = "white" if self.black_turn else "black"

        # change turns and draw screen
        self.black_turn = not self.black_turn
        self.draw()

    def draw(self):
        # draw stones - filled circle and antialiased ring
        self.clear_screen()        

        for col in range(self.size):
            for row in range(self.size):
                x, y = colrow_to_xy(col, row, self.size)
                if self.board[col][row] == 0:
                    continue
                color = WHITE
                if self.board[col][row] == -1:
                    color = RED
                    gfxdraw.aacircle(self.screen, x, y, STONE_RADIUS, color)
                    gfxdraw.filled_circle(self.screen, x, y, STONE_RADIUS, color)
                elif self.board[col][row] == -2:
                    gfxdraw.box(self.screen, pygame.Rect(x, y, 20, 20), WHITE)
                else:
                    self.figures[int(self.board[col][row] - 1)].draw(x, y)                    
        

        if self.simulate_mode and self.curr_id >= 0:
            score_msg = (
                f"Aktuelle Figur: {self.figures[self.curr_id]}"
            )
            txt = self.font.render(score_msg, True, BLACK)
            self.screen.blit(txt, SCORE_POS)
            
        turn_msg = (
            f"{'Simulationsmodus' if self.simulate_mode else 'Baumodus'}. "
            + "Klick: Figur plazieren, Z: Ziel, X: Unb.felder, Enter: Simulation"
        )
        txt = self.font.render(turn_msg, True, BLACK)
        self.screen.blit(txt, TURN_POS)

        pygame.display.flip()

    def simulate(self):
        print('Simulate')
        if not self.simulate_mode:
            if not self.zielfeld:
                print('Ziel muss gesetzt werden')
                return
            if len(self.figures) == 0:
                print('Keine Figuren platziert; zumindest eine muss her, bitch')
                return
            self.simulate_mode = True
            self.curr_id = -1

            for col, row in zip(*np.where(self.board == -1)):
                self.graph.remove_node((col, row))
                print('Removing ', (col, row))

            print(self.graph.nodes())
            print(self.graph.edges())
            self.draw()            
            return

        self.curr_id = (self.curr_id + 1) % len(self.figures)
        curr_fig = self.figures[self.curr_id]

        print('Figure ', curr_fig.id)

        curr_node = (curr_fig.col, curr_fig.row)
        paths = nx.all_shortest_paths(self.graph, source=curr_node, target=self.zielfeld)        
        for p in paths:
            print(len(p), ':', p)
            num_pos = random.randint(1, 6)
            print('Würfel', num_pos)
            new_node = p[min(len(p) - 1, num_pos)]
            print('Neue Position', new_node)
            self.board[curr_fig.col, curr_fig.row] = 0
            curr_fig.set_pos(new_node[0], new_node[1])
            self.board[new_node[0], new_node[1]] = curr_fig.id
            break

        self.draw()

    def update(self):
        # TODO: undo button
        events = pygame.event.get()
        for event in events:
            if event.type == pygame.MOUSEBUTTONUP:
                self.handle_click()
            if event.type == pygame.QUIT:
                sys.exit()
            if event.type == pygame.KEYUP:
                if event.key == pygame.K_p:
                    self.pass_move()
                if event.key == pygame.K_x:
                    self.block()                
                if event.key == pygame.K_z:
                    self.ziel()
                if event.key == pygame.K_RETURN:
                    self.simulate()
        

if __name__ == "__main__":
    g = Game(size=10)
    g.init_pygame()
    g.clear_screen()
    g.draw()

    while True:
        g.update()
        pygame.time.wait(100)
