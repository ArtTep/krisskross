import os
import random
from flask import Flask, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "http://127.0.0.1:8000"}})

GRID_SIZE = 12  # Crossword-like grid
MAX_ATTEMPTS = 300  # More attempts to ensure better placement

def generate_numbers():
    """ Generate random numbers between 3-6 digits """
    lengths = [random.randint(3, 6) for _ in range(12)]
    return [str(random.randint(10**(l-1), 10**l - 1)) for l in lengths]

def create_empty_grid(size):
    """ Create an empty crossword grid filled with spaces """
    return [[' ' for _ in range(size)] for _ in range(size)]

def has_intersection(grid, row, col, direction, length):
    """ Ensure every number intersects with at least one other """
    if direction == "H":
        return any(grid[row][col + i] == "*" for i in range(length))
    if direction == "V":
        return any(grid[row + i][col] == "*" for i in range(length))
    return False

def is_valid_placement(grid, num, row, col, direction):
    """ Check if placement is valid with enforced crossword-style rules """
    length = len(num)

    if direction == "H":
        if col + length > GRID_SIZE:
            return False  # Out of bounds
        if any(grid[row][col + i] not in (' ', '*') for i in range(length)):
            return False  # Collision

        # Prevent horizontal stacking
        if row > 0 and any(grid[row - 1][col + i] == "*" for i in range(length)):
            return False
        if row < GRID_SIZE - 1 and any(grid[row + 1][col + i] == "*" for i in range(length)):
            return False

        # Must intersect or extend from an existing word
        return has_intersection(grid, row, col, "H", length) or col == 0

    elif direction == "V":
        if row + length > GRID_SIZE:
            return False  # Out of bounds
        if any(grid[row + i][col] not in (' ', '*') for i in range(length)):
            return False  # Collision

        # Prevent vertical stacking
        if col > 0 and any(grid[row + i][col - 1] == "*" for i in range(length)):
            return False
        if col < GRID_SIZE - 1 and any(grid[row + i][col + 1] == "*" for i in range(length)):
            return False

        # Must intersect or extend from an existing word
        return has_intersection(grid, row, col, "V", length) or row == 0

    return False

def place_number(grid, num):
    """ Try placing a number with proper connections """
    placed = False
    attempts = 0
    length = len(num)

    while not placed and attempts < MAX_ATTEMPTS:
        row, col = random.randint(0, GRID_SIZE - 1), random.randint(0, GRID_SIZE - 1)
        direction = random.choice(["H", "V"])

        if is_valid_placement(grid, num, row, col, direction):
            for i in range(length):
                if direction == "H":
                    grid[row][col + i] = "*"  # Each digit spans a separate box
                else:
                    grid[row + i][col] = "*"
            placed = True

        attempts += 1

    return placed

def generate_puzzle():
    """ Generate a crossword-style number puzzle with enforced connections """
    grid = create_empty_grid(GRID_SIZE)
    numbers = generate_numbers()
    placed_numbers = []

    first_num = numbers.pop(0)
    row, col = GRID_SIZE // 2, GRID_SIZE // 2  # Start near center
    place_number(grid, first_num)
    placed_numbers.append(first_num)

    for num in numbers:
        if place_number(grid, num):
            placed_numbers.append(num)

    return grid, placed_numbers

@app.route('/generate', methods=['GET'])
def generate():
    puzzle, numbers = generate_puzzle()
    return jsonify({"puzzle": puzzle, "numbers": numbers})

from flask import send_from_directory

@app.route('/')
def serve_index():
    return send_from_directory('static', 'index.html')

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))  # Use Render’s dynamic port
    app.run(host='0.0.0.0', port=port, debug=True)
