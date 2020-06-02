from rgtk.BitSet import BitSet
from rgtk.constraint_solver import ConstraintSolver
from rgtk.Interval import Interval
from rgtk.IntervalsToBitSetsEvaluator import IntervalsToBitSetsEvaluator


intervals = []
interval_font = Interval.create_fixed_length_at_start_point(begin=20, length=96)
interval_player_sprite = Interval(begin=0, end=255, length=6)
interval_enemy_sprite = Interval(begin=0, end=255, length=2)
interval_bg1 = Interval(begin=0, end=447, length=1)
interval_bg2 = Interval(begin=256, end=447, length=1)
interval_bg3 = Interval(begin=256, end=447, length=1)
intervals.append(interval_font)
intervals.append(interval_player_sprite)
intervals.append(interval_enemy_sprite)
intervals.append(interval_bg1)
intervals.append(interval_bg2)
intervals.append(interval_bg3)

bitsets = []
VRAMPositions = BitSet(448)
bitsets.append(VRAMPositions)

interval_to_VRAM_solver = ConstraintSolver(sources=intervals, destinations=bitsets, evaluator_class=IntervalsToBitSetsEvaluator, debugging=True)
while (len(interval_to_VRAM_solver.solutions) == 0) and (interval_to_VRAM_solver.is_exhausted() == False):
    interval_to_VRAM_solver.update()

# How'd the solution go?
solution = interval_to_VRAM_solver.solutions[0]
for move in solution:
    # The "source" will be one of our intervals, and since we're only doing one BitSet, our "destination" will always be the VRAMPositions array.
    # Dig into the change list to figure out which slot was actually chosen.
    source_interval = intervals[move.source_index]
    dest_interval = move.change_list.chosen_interval
    if dest_interval.begin == dest_interval.end:
        print(f"Interval {move.source_index}: ({source_interval.begin}, {source_interval.end}) with length {source_interval.length} will occupy location {dest_interval.begin}.")
    else:
        print(f"Interval {move.source_index}: ({source_interval.begin}, {source_interval.end}) with length {source_interval.length} will occupy locations {dest_interval.begin} thru {dest_interval.end}")

print("Done!")
