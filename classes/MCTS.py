import random, math, copy, gc, asyncio
from .tilemap import TileMap
from customEnums import TileState, GameState

class FastBoard:
    """Ultra-lightweight integer representation for MCTS simulations."""
    __slots__ = ('rows', 'cols', 'grid', 'turn', 'state', 'moves_left')

    def __init__(self, rows, cols, grid, turn, state):
        self.rows = rows
        self.cols = cols
        self.grid = grid  # 2D list of integers (0: None, 1: Red, 2: Blue)
        self.turn = turn  # 1: Red, 2: Blue
        self.state = state # GameState enum
        self.moves_left = sum(row.count(0) for row in grid)

    @classmethod
    def from_tilemap(cls, tilemap):
        # grid[col][row]
        grid = [[0 for _ in range(tilemap.rows)] for _ in range(tilemap.columns)]
        for (c, r), tile in tilemap.tilesDictionary.items():
            if tile.state == TileState.RED:
                grid[c][r] = 1
            elif tile.state == TileState.BLUE:
                grid[c][r] = 2

        turn = 1 if tilemap.turn == TileState.RED else 2
        return cls(tilemap.rows, tilemap.columns, grid, turn, tilemap.state)

    def clone(self):
        return FastBoard(
            self.rows, 
            self.cols, 
            [col[:] for col in self.grid], 
            self.turn, 
            self.state
        )

    def get_legal_columns(self):
        if self.state != GameState.PLAYING:
            return []
        # Column is valid if top row (index 0) is empty
        return [c for c in range(self.cols) if self.grid[c][0] == 0]
    

    def place_piece(self, col):
        for r in range(self.rows - 1, -1, -1):
            if self.grid[col][r] == 0:
                self.grid[col][r] = self.turn
                self.moves_left -= 1
                
                # Check for win
                if self._check_win(r, col, self.turn):
                    self.state = GameState.REDWIN if self.turn == 1 else GameState.BLUEWIN
                elif self.moves_left == 0:
                    self.state = GameState.DRAW
                else:
                    self.turn = 2 if self.turn == 1 else 1
                return (col, r)
        return None


    def undo_piece(self, col, r, prev_turn, prev_state):
        self.grid[col][r] = 0
        self.moves_left += 1
        self.turn = prev_turn
        self.state = prev_state

    def _check_win(self, r, c, player):
        directions = [(0, 1), (1, 0), (1, 1), (1, -1)]
        for dr, dc in directions:
            count = 1
            # Forward
            nr, nc = r + dr, c + dc
            while 0 <= nr < self.rows and 0 <= nc < self.cols and self.grid[nc][nr] == player:
                count += 1
                nr += dr
                nc += dc
            # Backward
            nr, nc = r - dr, c - dc
            while 0 <= nr < self.rows and 0 <= nc < self.cols and self.grid[nc][nr] == player:
                count += 1
                nr -= dr
                nc -= dc
            if count >= 4:
                return True
        return False


    def find_tactical_move(self, legal_cols):
        """Checks for instant winning moves or mandatory blocks."""
        opponent = 2 if self.turn == 1 else 1
        block_move = None

        for col in legal_cols:
            # Find the row the piece would land on
            for r in range(self.rows - 1, -1, -1):
                if self.grid[col][r] == 0:
                    # 1. Can WE win right now?
                    if self._check_win(r, col, self.turn):
                        return col
                    # 2. Can the OPPONENT win here next turn? (Save as block move)
                    if block_move is None and self._check_win(r, col, opponent):
                        block_move = col
                    break

        return block_move


class MCTSNode:
    def __init__(self, parent=None, move=None, untried_moves=None):
        self.parent = parent
        self.move = move  # (col, row) or col
        self.children = []
        self.untried_moves = untried_moves if untried_moves is not None else []
        self.visits = 0
        self.total_reward = 0.0

    def ucb1_value(self, exploration_constant=math.sqrt(2.0)):
        if self.visits == 0:
            return float("inf")
        avg = self.total_reward / self.visits
        parent_visits = self.parent.visits if self.parent is not None else 1
        return avg + exploration_constant * math.sqrt(math.log(parent_visits) / self.visits)

    def select_child(self):
        return max(self.children, key=lambda child: child.ucb1_value())

    def add_child(self, col, move_coord, untried_moves):
        self.untried_moves.remove(col)
        child = MCTSNode(parent=self, move=move_coord, untried_moves=untried_moves)
        self.children.append(child)
        return child

    def update(self, reward):
        self.visits += 1
        self.total_reward += reward

    def cleanup(self):
        for child in self.children:
            child.cleanup()
        self.children.clear()
        self.untried_moves.clear()
        self.parent = None


def free_mcts_memory(root_node: MCTSNode):
    if root_node is not None:
        root_node.cleanup()


async def mcts_search(root_board, team_color: TileState, iterations=400):
    # Convert Pygame TileMap into integer-only board once
    fast_root = FastBoard.from_tilemap(root_board)
    root_node = MCTSNode(untried_moves=fast_root.get_legal_columns())



    for i in range(iterations):
        node = root_node
        sim_board = fast_root.clone()

        # 1. Selection
        while not node.untried_moves and node.children and sim_board.state == GameState.PLAYING:
            node = node.select_child()
            col = node.move[0] if isinstance(node.move, (tuple, list)) else node.move
            sim_board.place_piece(col)

        # 2. Expansion
        if node.untried_moves and sim_board.state == GameState.PLAYING:
            col = random.choice(node.untried_moves)
            coord = sim_board.place_piece(col)
            node = node.add_child(col, coord, sim_board.get_legal_columns())

        # 3. Simulation (Pure integer loop - blazing fast in WebAssembly)
        while sim_board.state == GameState.PLAYING:
            legal = sim_board.get_legal_columns()
            if not legal:
                break

            col = random.choice(legal)
            sim_board.place_piece(col)

        # Reward determination
        winner = sim_board.state
        if winner == GameState.BLUEWIN:
            reward = 1.0 if team_color == TileState.BLUE else 0.0
        elif winner == GameState.REDWIN:
            reward = 1.0 if team_color == TileState.RED else 0.0
        else:
            reward = 0.5

        # 4. Backpropagation
        while node is not None:
            node.update(reward)
            node = node.parent

        # Yield to Pygame every 25 iterations to maintain 60 FPS
        if i % 15 == 0:
            await asyncio.sleep(0)

    if not root_node.children:
        free_mcts_memory(root_node)
        return None, {}, 0.0

    # Format output for your TileMap UI
    stats = {}
    for child in root_node.children:
        col = child.move[0] if isinstance(child.move, (list, tuple)) else child.move
        win_rate = (child.total_reward / child.visits) if child.visits > 0 else 0.0
        stats[col] = {
            "visits": child.visits,
            "win_rate": win_rate
        }

    best_child = max(root_node.children, key=lambda child: child.visits)
    best_move = best_child.move
    ucb_score = best_child.ucb1_value()

    free_mcts_memory(root_node)

    return best_move, stats, ucb_score