import pygame, random, math, copy, gc, asyncio
from pygame.math import Vector2
from .tilemap import TileMap
from .tile import Tile
from customEnums import TileState, GameState

class MCTSNode:
    def __init__(self, board: TileMap, parent = None, move: Vector2 = None):
        self.board = board
        self.parent = parent
        self.move = move
        self.children = []

        self.untried_moves = board.getLegalMove() if board.state == GameState.PLAYING else []

        self.visits = 0
        self.total_reward = 0.0


    def ucb1_value(self, exploration_constant = math.sqrt(2.0)):
        if self.visits == 0:
            return float("inf")

        average_reward = self.total_reward / self.visits
        parent_visits = self.parent.visits if self.parent is not None else 1

        return average_reward + exploration_constant * math.sqrt(math.log(parent_visits) / self.visits)

    def select_child(self):
        return max(self.children, key = lambda child: child.ucb1_value())

    def add_child(self, move: list[tuple[int,int]], board: TileMap):
        self.untried_moves.remove(move)

        child = MCTSNode(board, parent=self, move=move)
        self.children.append(child)
        return child

    def update(self, reward):
        self.visits += 1
        self.total_reward += reward

    def cleanup(self):
        """Recursively clears links across the MCTS tree to prevent memory leaks."""
        # 1. Clear all children recursively
        for child in self.children:
            child.cleanup()
        
        # 2. Break references on this node
        self.children.clear()
        self.untried_moves.clear()
        self.parent = None
        self.board = None  # Breaks reference to cloned TileMap/Pygame surfaces



def free_mcts_memory(root_node: MCTSNode):
    """Destroys the tree and forces immediate memory reclamation."""
    if root_node is not None:
        root_node.cleanup()
        del root_node
    
    # Force Python's cyclic garbage collector to purge unreferenced objects
    gc.collect()

async def mcts_search(root_board: TileMap, team_color: TileState, iterations = 500):
    root_node = MCTSNode(root_board)

    for i in range(iterations):
        if i % 25 == 0:
            await asyncio.sleep(0)

        node = root_node
        board = root_node.board.clone()

        # 1. Selection
        while not node.untried_moves and node.children and board.state == GameState.PLAYING:
            node = node.select_child()
            board.place_at_columns(node.move)

        # 2. Expansion
        if node.untried_moves and board.state == GameState.PLAYING:
            move = random.choice(node.untried_moves)
            board.place_at_columns(move)
            node = node.add_child(move, board)

        # 3. Simulation
        while board.state == GameState.PLAYING:
            moves = board.getLegalMove()
            move = random.choice(moves)
            board.place_at_columns(move)

        # Reward determination
        winner = board.state
        if winner == GameState.BLUEWIN:
            reward = 1.0 if team_color == TileState.BLUE else 0
        elif winner == GameState.REDWIN:
            reward = 1.0 if team_color == TileState.RED else 0
        else:
            reward = 0.5

        # 4. Backpropagation
        while node is not None:
            node.update(reward)
            node = node.parent

    if not root_node.children:
        return None


    # Collect per-column stats directly from root children
    stats = {}
    for child in root_node.children:
        col = child.move[0] if isinstance(child.move, (list, tuple)) else child.move
        win_rate = (child.total_reward / child.visits) if child.visits > 0 else 0.0
        stats[col] = {
            "visits": child.visits,
            "win_rate": win_rate
        }

    # Best move & UCB score
    best_child = max(root_node.children, key=lambda child: child.visits)
    best_move = best_child.move
    ucb_score = best_child.ucb1_value()

    # Free memory
    free_mcts_memory(root_node)
    root_node = None

    return best_move, stats, ucb_score