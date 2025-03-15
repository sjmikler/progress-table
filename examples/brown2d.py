#  Copyright (c) 2022-2025 Szymon Mikler
#  Licensed under the MIT License

import math
import random
import time

from progress_table import ProgressTable


def calc_distance(pos):
    return (pos[0] ** 2 + pos[1] ** 2) ** 0.5


def get_color_by_distance(distance):
    if distance < 20:
        return "white"
    elif distance < 40:
        return "cyan"
    elif distance < 60:
        return "blue"
    elif distance < 80:
        return "magenta"
    elif distance < 100:
        return "red"
    else:
        return "yellow bold"


def shift_rows_up(table, last_row_color):
    num_rows = table.num_rows()
    num_columns = table.num_columns()

    for row in range(num_rows - 1):
        for col in range(num_columns):
            table.at[row, col] = table.at[row + 1, col]
            table.at[row, col, "color"] = table.at[row + 1, col, "color"]
    for col in range(num_columns):
        table.at[-2, col, "color"] = last_row_color


def main(random_seed=None, sleep_duration=0.001, **overrides):
    if random_seed is None:
        random_seed = random.randint(0, 100)
    random.seed(random_seed)

    table = ProgressTable(
        pbar_embedded=False,
        pbar_style="full clean blue",
        **overrides,
    )

    TARGET_DISTANCE = 100

    PARTICLE_VELOCITY = 1
    PARTICLE_MOMENTUM = 0.999

    MAX_ROWS = 20
    STEP_SIZE = 100

    distance_pbar = table.pbar(
        TARGET_DISTANCE,
        description="Distance",
        show_throughput=False,
        show_progress=True,
    )

    current_position = (0, 0)
    current_velocity = PARTICLE_VELOCITY

    print("Particle will move randomly in 2D space.")
    print(f"Simulation stops when it reaches distance of {TARGET_DISTANCE} from the center.")

    tick = 0
    pbar_momentum = 0
    while calc_distance(current_position) < TARGET_DISTANCE:
        random_direction = random.uniform(0, 2 * 3.1415)
        new_velocity = random.uniform(0, PARTICLE_VELOCITY * 2)
        current_velocity = current_velocity * PARTICLE_MOMENTUM + new_velocity * (1 - PARTICLE_MOMENTUM)
        move_vector = (
            current_velocity * math.cos(random_direction),
            current_velocity * math.sin(random_direction),
        )
        current_position = (
            current_position[0] + move_vector[0],
            current_position[1] + move_vector[1],
        )
        distance_from_center = calc_distance(current_position)

        tick += 1
        table["tick"] = tick
        table["velocity"] = current_velocity
        table["position X"] = current_position[0]
        table["position Y"] = current_position[1]
        table["distance from center"] = distance_from_center

        pbar_momentum = pbar_momentum * 0.95 + int(distance_from_center) * 0.05
        distance_pbar.set_step(round(pbar_momentum))

        if tick % STEP_SIZE == 0:
            color = get_color_by_distance(distance_from_center)
            if table.num_rows() > MAX_ROWS:
                shift_rows_up(table, last_row_color=color)
            else:
                table.next_row(color=color)

        time.sleep(sleep_duration)

    color = get_color_by_distance(100)
    table.next_row(color=color)
    table.close()


if __name__ == "__main__":
    main()
