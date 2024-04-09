#  Copyright (c) 2022-2024 Szymon Mikler

import math
import random
import time

from progress_table import ProgressTable


def calc_distance(pos):
    return (pos[0] ** 2 + pos[1] ** 2) ** 0.5


def main(**overrides):
    table = ProgressTable(
        **overrides,
    )

    TARGET_DISTANCE = 100

    PARTICLE_VELOCITY = 1
    PARTICLE_MOMENTUM = 0.999

    SLEEP = 0.001
    MAX_ROWS = 30

    distance_pbar = table.pbar(TARGET_DISTANCE, description="Distance", show_throughput=False, show_progress=True)

    current_position = (0, 0)
    current_velocity = PARTICLE_VELOCITY

    print("Simulating brownian motions!")
    print(f"Simulation will end when {TARGET_DISTANCE} distance is exceeded!")

    tick = 0
    while calc_distance(current_position) < TARGET_DISTANCE:
        random_direction = random.uniform(0, 2 * 3.1415)
        new_velocity = random.uniform(0, PARTICLE_VELOCITY * 2)
        current_velocity = current_velocity * PARTICLE_MOMENTUM + new_velocity * (1 - PARTICLE_MOMENTUM)
        move_vector = (current_velocity * math.cos(random_direction), current_velocity * math.sin(random_direction))
        current_position = (current_position[0] + move_vector[0], current_position[1] + move_vector[1])
        distance_from_center = calc_distance(current_position)

        row = tick % MAX_ROWS
        tick += 1
        table["tick", row] = tick
        table["velocity", row] = current_velocity
        table["position X", row] = current_position[0]
        table["position Y", row] = current_position[1]
        table["distance from center", row] = distance_from_center
        distance_pbar.reset(total=int(distance_from_center))

        if table.num_rows() < MAX_ROWS:
            table.next_row()
        time.sleep(SLEEP)

    row = (tick - 1) % MAX_ROWS
    table.at[:row, :, "C"] = "blue"
    table.at[row, :, "C"] = "blue bold"
    table.close()


if __name__ == "__main__":
    main()
