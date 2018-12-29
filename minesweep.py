import random
import time

BOARD_SIZE = 11  # Square on edges for this simplification
NUM_MINES = 15  # 30 / 225 should be reasonable.


class Cell(object):
    def __init__(self, x, y, board_width, board_height):
        self.x = x
        self.y = y
        self.board_width = board_width
        self.board_height = board_height
        self.value = 0  # No bomb, no neighboring bombs
        self.neighbor_coords = [
            (i + self.x, j + self.y)
            for i in range(-1, 2)
            for j in range(-1, 2)
            if 0 <= i + self.x < self.board_width
            and 0 <= j + self.y < self.board_height
            and not (i == self.x and j == self.y)
        ]
        self.is_visible = False
        self.is_flagged = False

    def get_side_neighbors(self):
        return [n for n in self.neighbor_coords if (n[0] == self.x or n[1] == self.y)]

    def get_all_neighbors(self):
        return self.neighbor_coords

    def set_bomb(self):
        if self.value == -1:
            return False
        else:
            self.value = -1
            return self.neighbor_coords

    @property
    def is_bomb(self):
        return self.value == -1

    def toggle_flag(self):
        self.is_flagged = not self.is_flagged
        return "flagged" if self.is_flagged else "cleared"

    @property
    def is_correct(self):
        return self.is_bomb == self.is_flagged

    def increment(self):
        if self.value == -1:
            # Is already a bomb, so no need for neighbor numbers
            return
        elif self.value == 8:
            # Something went wrong. Can't have more than 8 neighboring bombs
            raise AssertionError("Cannot have more than 8 neighboring bombs")
        else:
            self.value += 1

    def __str__(self):
        if self.is_flagged:
            return "F"
        if not self.is_visible:
            return "?"
        if self.value == 0:
            return " "
        elif self.value == -1:
            return "X"
        else:
            return str(self.value)


class GameBoard(object):
    def __init__(self, board_size, num_mines):
        self.width, self.height = board_size
        self.num_mines = num_mines

        self.board = [
            Cell(x, y, self.width, self.height)
            for y in range(self.width)
            for x in range(self.height)
        ]

        mines_left = self.num_mines
        while mines_left > 0:
            new_bomb = random.randint(0, self.width * self.height - 1)
            neighbors = self.board[new_bomb].set_bomb()
            if neighbors:
                for neighbor in self.flatten(neighbors):
                    self.board[neighbor].increment()
                mines_left -= 1

        self.is_lost = False

    def flatten(self, cells):
        indices = []
        if not isinstance(cells, list):
            cells = [cells]
        for cell in cells:
            x, y = cell
            indices.append(x + y * self.width)
        if len(indices) == 1:
            return indices[0]
        return indices

    @property
    def is_won(self):
        for cell in self.board:
            if not cell.is_correct:
                return False
        return True

    def __str__(self):
        board_str = "    "
        for i in range(self.width):
            board_str += str(i).center(4, " ")
        board_str += "\n"
        board_str += "   " + "----" * (self.width) + "-\n"
        for y in range(self.height):
            board_str += str(y).center(3)
            for x in range(self.width):
                value = str(self.board[self.flatten((x, y))])
                if x == 0:
                    board_str += "|"
                board_str += f" {value} |"
            board_str += "\n" + "   " + "----" * (self.width) + "-\n"
        return board_str.rstrip()

    def is_valid_cell(self, x, y):
        return self.flatten((x, y)) <= len(self.board)

    def explode_cell(self, x, y):
        index = self.flatten((x, y))
        # If it's a bomb, explode and lose the game
        if self.board[index].is_bomb:
            for cell in self.board:
                cell.is_visible = True
            self.is_lost = True
            return "a bomb!!"
        else:
            # Could be either blank (expose all neighbors) or number (only expose self)
            checked = []  # Haven't checked any cells yet
            to_check = [
                self.board[index]
            ]  # Initially need to check at least the chosen cell
            while len(to_check) > 0:  # Loop until no more cells need to be checked
                cell = to_check.pop()  # Get the first cell that needs to be checked
                if cell in checked:
                    continue  # Already checked, skip it
                if not cell.is_bomb and not cell.is_flagged:
                    cell.is_visible = True
                    checked.append(cell)
                    # If this was empty cell, expose neighbors.
                    # If it was a number, leave it exposed, but ignore neighbors
                    if cell.value == 0:  # Empty
                        touching_cells = [
                            self.board[self.flatten(n)]
                            for n in cell.get_all_neighbors()
                        ]
                        to_check.extend([n for n in touching_cells if n.value >= 0])
            return "not a bomb. Whew!"

    def _try_parse_input(self, in_str):
        tokens = in_str.replace(" ", ",").split(",")
        # Too many tokens:
        if len(tokens) > 3:
            return False, f"Too many tokens in input string: {in_str}"
        if len(tokens) < 3:
            return False, f"Not enough tokens in input string: {in_str}"
        cmd = tokens[0].upper()
        try:
            x = int(tokens[1])
            y = int(tokens[2])
        except ValueError:
            # Either x or y was not an integer
            return False, f"Invalid numeric points in input: {in_str}"
        return True, (cmd, x, y)

    def execute_move(self, in_str):
        # Parse input and check for possibly valid command and point
        success, val = self._try_parse_input(in_str)
        if not success:
            return val
        else:
            cmd, x, y = val

        # Coordinates must be inside the board
        if not self.is_valid_cell(x, y):
            return "Point is not on the board (remember, it's zero-based)"
        # Command must be known
        if cmd not in ["F", "X"]:
            return f"Unknown command '{cmd}': " + in_str

        if cmd == "F":
            flag_state = self.toggle_flag(x, y)
            return f"({x}, {y}) is " + flag_state
        elif cmd == "X":
            result = self.explode_cell(x, y)
            return f"({x}, {y}) was " + result

    def toggle_flag(self, x, y):
        return self.board[self.flatten((x, y))].toggle_flag()

    def _incorrect_cells(self):
        return [(cell.x, cell.y) for cell in self.board if not cell.is_correct]


if __name__ == "__main__":
    print("Valid moves are [(F)lag, (X)plode] x, y (zero-indexed)")
    game = GameBoard((BOARD_SIZE, BOARD_SIZE), NUM_MINES)
    start_time = time.time()
    while not game.is_won and not game.is_lost:
        print(game)
        user_input = input("\nEnter next move: ")
        if user_input.upper()[0] == "Q":
            print("Quitting...")
            break
        result = game.execute_move(user_input)
        print(result)
    else:
        print(game)
        game_duration = time.time() - start_time
        if game.is_won:
            print(f"You won in {int(game_duration)} seconds!")
        else:
            print(f"You lost after {int(game_duration)} seconds :(")

