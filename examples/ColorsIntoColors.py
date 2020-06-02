from rgtk.ColorEntry import ColorEntry
from rgtk.ColorsIntoColorsEvaluator import ColorsIntoColorsEvaluator
from rgtk.constraint_solver import ConstraintSolver

# Source nodes
source_node_list = []

src_red_1 = ColorEntry()
src_red_1.intentions.attempt_set_intention(ColorEntry.INTENTION_COLOR, (255,0,0))
src_red_1.intentions.attempt_set_intention(ColorEntry.INTENTION_SLOT, 1)
source_node_list.append(src_red_1)

src_red_3 = ColorEntry()
src_red_3.intentions.attempt_set_intention(ColorEntry.INTENTION_COLOR, (255,0,0))
src_red_3.intentions.attempt_set_intention(ColorEntry.INTENTION_SLOT, 3)
source_node_list.append(src_red_3)

src_green_2 = ColorEntry()
src_green_2.intentions.attempt_set_intention(ColorEntry.INTENTION_COLOR, (0,255,0))
src_green_2.intentions.attempt_set_intention(ColorEntry.INTENTION_SLOT, 2)
source_node_list.append(src_green_2)

src_blue = ColorEntry()
src_blue.intentions.attempt_set_intention(ColorEntry.INTENTION_COLOR, (0,0,255))
source_node_list.append(src_blue)

src_yellow = ColorEntry()
src_yellow.intentions.attempt_set_intention(ColorEntry.INTENTION_COLOR, (255,255,0))
source_node_list.append(src_yellow)

# Dest nodes
dest_node_list = []

dest_blue_0 = ColorEntry()
dest_blue_0.intentions.attempt_set_intention(ColorEntry.INTENTION_COLOR, (0,0,255))
dest_blue_0.intentions.attempt_set_intention(ColorEntry.INTENTION_SLOT, 0)
dest_node_list.append(dest_blue_0)

dest_green = ColorEntry()
dest_green.intentions.attempt_set_intention(ColorEntry.INTENTION_COLOR, (0,255,0))
dest_node_list.append(dest_green)

dest_red = ColorEntry()
dest_red.intentions.attempt_set_intention(ColorEntry.INTENTION_COLOR, (255,0,0))
dest_node_list.append(dest_red)

dest_clear_1 = ColorEntry()
dest_node_list.append(dest_clear_1)

dest_clear_2 = ColorEntry()
dest_node_list.append(dest_clear_2)

# Start the solver.
solver = ConstraintSolver(source_node_list, dest_node_list, ColorsIntoColorsEvaluator, True)

while False == solver.is_exhausted():
    solver.update()

solutions = solver.solutions

print(f"Found {len(solutions)} colors-into-colors solutions.")

