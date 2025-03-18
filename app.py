import os
import random
from flask import Flask, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "http://127.0.0.1:8000"}})

GRID_SIZE = 12  # Crossword-like grid
MAX_ATTEMPTS = 200  # Allow more placement attempts

def generate_numbers():
    """ Generate random numbers between 3-6 digits """
    lengths = [random.randint(3, 6) for _ in range(12)]  # Generate 12 numbers
    return [str(random.randint(10**(l-1), 10**l - 1)) for l in lengths]

def create_empty_grid(size):
    """ Create an empty crossword grid filled with spaces """
    return [[' ' for _ in range(size)] for _ in range(size)]

def can_place_number(grid, num, row, col, direction):
    """ Check if a number can be placed while ensuring intersections """
    length = len(num)
    has_intersection = False

    if direction == "H":
        if col + length > GRID_SIZE:
            return False

        for i in range(length):
            if grid[row][col + i] != ' ' and grid[row][col + i] != "*":
                return False  # Prevent overwriting numbers
            if grid[row][col + i] == "*":
                has_intersection = True

        return has_intersection or col == 0  # Allow placement at the start

    elif direction == "V":
        if row + length > GRID_SIZE:
            return False

        for i in range(length):
            if grid[row + i][col] != ' ' and grid[row + i][col] != "*":
                return False
            if grid[row + i][col] == "*":
                has_intersection = True

        return has_intersection or row == 0

    return False

def place_number(grid, num):
    """ Try placing a number ensuring some intersections and avoiding direct stacking """
    placed = False
    attempts = 0
    length = len(num)

    while not placed and attempts < MAX_ATTEMPTS:
        row, col = random.randint(1, GRID_SIZE - length - 1), random.randint(1, GRID_SIZE - length - 1)
        direction = random.choice(["H", "V"])
        has_intersection = False

        if direction == "H":
            if col + length > GRID_SIZE:
                attempts += 1
                continue

            # Ensure spacing by checking above and below
            if any(grid[row][c] == "*" for c in range(col, col + length)) or \
               any(grid[row - 1][c] == "*" for c in range(col, col + length) if row > 0) or \
               any(grid[row + 1][c] == "*" for c in range(col, col + length) if row < GRID_SIZE - 1):
                attempts += 1
                continue

            # Allow some numbers to be independent (not force every one to intersect)
            has_intersection = any(grid[row][c] == "*" for c in range(col, col + length))
            if not has_intersection and random.random() > 0.4:  # 60% chance to require intersection
                attempts += 1
                continue

            for i in range(length):
                grid[row][col + i] = "*"
            placed = True

        elif direction == "V":
            if row + length > GRID_SIZE:
                attempts += 1
                continue

            # Ensure spacing by checking left and right
            if any(grid[r][col] == "*" for r in range(row, row + length)) or \
               any(grid[r][col - 1] == "*" for r in range(row, row + length) if col > 0) or \
               any(grid[r][col + 1] == "*" for r in range(row, row + length) if col < GRID_SIZE - 1):
                attempts += 1
                continue

            # Allow some independent numbers
            has_intersection = any(grid[r][col] == "*" for r in range(row, row + length))
            if not has_intersection and random.random() > 0.4:  # 60% chance to require intersection
                attempts += 1
                continue

            for i in range(length):
                grid[row + i][col] = "*"
            placed = True

        attempts += 1

    return placed


def generate_puzzle():
    """ Generate a crossword-style number puzzle with proper intersections """
    grid = create_empty_grid(GRID_SIZE)
    numbers = generate_numbers()
    placed_numbers = []

    first_num = numbers.pop(0)
    row, col = GRID_SIZE // 2, GRID_SIZE // 2  # Start near the center
    place_number(grid, first_num)
    placed_numbers.append(first_num)

    for num in numbers:
        if place_number(grid, num):
            placed_numbers.append(num)

    # 🔥 If less than 8 numbers were placed, allow it to return (no recursion)
    if len(placed_numbers) < 8:
        print("⚠ Not enough numbers placed! Returning as-is.")
        return grid, placed_numbers  # Return even if fewer numbers are placed

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
