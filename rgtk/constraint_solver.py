import math
import copy
from typing import List, Tuple

from rgtk.BitSet import BitSet
from rgtk.FSM import FSM, State
from rgtk.SimpleTimer import SimpleTimer

class Move:
    def __init__(self, source_index: int, dest_index: int, change_list: object):
        self.source_index = source_index
        self.dest_index = dest_index
        self.change_list = change_list


class Evaluator:
    def __init__(self, source_index: int, source: object):
        self.source_index = source_index
        self.source = source

    @classmethod
    def factory_constructor(cls, source_index: int, source: object) -> 'Evaluator':
        pass

    def get_list_of_best_moves(self) -> Tuple[int, List[Move]]:
        pass

    def update_moves_for_destination(self, destination_index: int, destination: object):
        pass

    @staticmethod
    def apply_changes(source: object, destination: object, change_list: object):
        pass

    @staticmethod
    def is_destination_empty(destination: object) -> bool:
        pass

class ConstraintSolver:
    # Static vars
    s_timer_names = [
          "ApplySolution"
        , "SolutionSuccessful"
        , "SubsetInit"
        , "AssessMoves"
        , "GetBestMoves"
        , "ExecuteMove"
    ]

    def __init__(self, sources: List[object], destinations: List[object], evaluator_class: any, debugging: any):
        # Create our timers.
        self.timer_name_to_timer = {}
        for name in ConstraintSolver.s_timer_names:
            self.timer_name_to_timer[name] = SimpleTimer(name)

        # Track our tree of solver nodes.
        # We'll start with an empty one.
        self._subset_tree_head = ConstraintSolver.SolverSubsetNode(parent=None, moves_list=[])

        # Now setup members.
        self.destinations = destinations
        self.sources = sources
        self._evaluator_class = evaluator_class
        self.solutions = []

        self._debugging = debugging

        # We'll let the first iteration of the solver pull from the WIP.
        self._current_subset_solver = None
        self._current_subset_solver_node = None

        # Create and start the state machine for this solver.
        self._fsm = FSM(self)
        self._fsm.start(ConstraintSolver.AssessCompletionState)

    # Returns true if all possible solutions have been found.
    def is_exhausted(self) -> bool:
        curr_state = self._fsm.get_current_state()
        if curr_state == ConstraintSolver.ExhaustedState:
            return True

        return False

    def update(self):
        self._fsm.update()

    # Applies a solution provided by the constraint solver to the original destination.
    # Returns a set of how sources are mapped to destinations.
    def apply_solution(self, solution: List[Move]):
        timer = self.timer_name_to_timer["ApplySolution"]
        timer.begin()

        for move in solution:
            source_index = move.source_index
            source = self.sources[source_index]

            dest_index = move.dest_index
            destination = self.destinations[dest_index]

            change_list = move.change_list

            self._evaluator_class.apply_changes(source, destination, change_list)

        timer.end()

    def _find_first_unvisited_node(self) -> 'ConstraintSolver.SubsetSolverNode':
        # Use a BFS approach to find the first univisited node.
        queue = [self._subset_tree_head]
        curr_node = None
        done = False
        while not done:
            curr_node = queue.pop(0)
            if curr_node.visited == False:
                # Found it!
                done = True
            else:
                # Add all children
                for child in curr_node.children:
                    queue.append(child)

        return curr_node

    def _create_subset_solver(self) -> 'ConstraintSolver.SubsetSolver':
        unmapped_sources_bitset = BitSet(len(self.sources))
        unmapped_sources_bitset.set_all()

        subset_solver = ConstraintSolver.SubsetSolver(parent_solver=self
            , sources=self.sources
            , wip_solution_state=self.destinations
            , unmapped_sources_bitset=unmapped_sources_bitset
            , evaluator_class=self._evaluator_class
            , indent_level=0
            , debugging=self._debugging)

        # Find our starting position using a BFS for each unvisited node.
        # For example, if this is our tree:
        # 0:       A
        # 1:   B   C   D
        # 2:  E F  G  HIJ
        # 3:  K   L M  N
        # 
        # ...our iteration will find ONE solution in the B tree, then one
        # solution in the C tree, then one in the D tree before moving on

        # Find first unvisited node.
        self._current_subset_solver_node = self._find_first_unvisited_node()

        # Apply moves from our parents before us.
        stack = []
        iter_node = self._current_subset_solver_node
        while iter_node is not None:
            stack.append(iter_node)
            iter_node = iter_node.parent

        while len(stack) > 0:
            node = stack.pop()
            for move in node.moves_list:
                subset_solver._execute_move(move)

        return subset_solver

    def _append_moves(self, subset_solver: 'ConstraintSolver.SubsetSolver', child_move_lists: List[List[Move]]):
        # Append this to our current tree.

        if len(child_move_lists) == 1:
            # If there's only one set of moves, add them to the node itself.
            move_list = child_move_lists[0]

            for move in move_list:
                self._current_subset_solver_node.moves_list.append(move)
                subset_solver._execute_move(move)
        else:
            # Need to create child nodes.
            for move_list in child_move_lists:
                child_node = ConstraintSolver.SolverSubsetNode(parent=self._current_subset_solver_node, moves_list=move_list)
                self._current_subset_solver_node.children.append(child_node)

            # Execute the leftmost child's actions so that 
            # we can continue using our current subset solver 
            # without having to create a new one.
            self._current_subset_solver_node = self._current_subset_solver_node.children[0]
            for move in self._current_subset_solver_node.moves_list:
                subset_solver._execute_move(move)

    def _remove_current_subset_solver(self) -> List[Move]:
        # Starting at the head, compile all moves for the solution.
        solution_moves = []

        # We'll assign the moves in order from head -> current.
        stack = []
        iter_node = self._current_subset_solver_node
        while iter_node is not None:
            stack.append(iter_node)
            iter_node = iter_node.parent

        while len(stack) > 0:
            node = stack.pop()
            child_moves = node.moves_list
            for child_move in child_moves:
                solution_moves.append(child_move)

        # Walk back up the tree, removing any node that has no children.
        curr_node = self._current_subset_solver_node.parent
        while len(curr_node.children) == 1:
            curr_node.children.pop()
            curr_node = curr_node.parent

        # Remove the current subset solver.
        self._current_subset_solver = None
        self._current_subset_solver_node = None

        # Consider our origin node as visited.
        unvisited = self._find_first_unvisited_node()
        unvisited.visited = True

        return solution_moves

    def _accept_current_subset_solver_as_successful(self):
        timer = self.timer_name_to_timer["SolutionSuccessful"]
        timer.begin()

        # Remove us and get the solutions.
        solution_moves = self._remove_current_subset_solver()
        self.solutions.append(solution_moves)

        timer.end()

    def _accept_current_subset_solver_as_failed(self):
        # Remove us.
        self._remove_current_subset_solver()

    class AssessCompletionState(State):
        @staticmethod
        def on_enter(context):
            if context._current_subset_solver is None:
                # Has our tree been exhausted?
                if context._subset_tree_head is None:
                    return ConstraintSolver.ExhaustedState
                else:
                    # Otherwise, we'll create a new subset solver from the tree.
                    subset_solver = context._create_subset_solver()
                    context._current_subset_solver = subset_solver
            return ConstraintSolver.AssessMovesState

    class AssessMovesState(State):
        @staticmethod
        def on_update(context):
            try:
                # Assess moves on current solver.
                context._current_subset_solver.assess_moves()
            except ConstraintSolver.AllItemsMappedSuccessfully:
                return ConstraintSolver.SuccessfulSubsetCompletionState
            else:
                return ConstraintSolver.SelectMovesState

    class SelectMovesState(State):
        @staticmethod
        def on_update(context):
            try:
                context._current_subset_solver.choose_next_moves()
            except ConstraintSolver.SolverFailed_NoMovesAvailableError:
                return ConstraintSolver.FailedSubsetCompletionState
            else:
                return ConstraintSolver.AssessMovesState

    class SuccessfulSubsetCompletionState(State):
        @staticmethod
        def on_enter(context):
            # Add the current solver as a solution.
            context._accept_current_subset_solver_as_successful()

            return ConstraintSolver.AssessCompletionState

    class FailedSubsetCompletionState(State):
        @staticmethod
        def on_enter(context):
            # Remove the current solver as failed.
            context._accept_current_subset_solver_as_failed()

            return ConstraintSolver.AssessCompletionState

    class ExhaustedState(State):
        pass

    class AllItemsMappedSuccessfully(Exception):
        pass

    class SolverFailed_NoMovesAvailableError(Exception):
        pass

    class SolverSubsetNode:
        def __init__(self, parent: 'ConstraintSolver.SolverSubsetTree', moves_list: List[Move]):
            self.parent = parent
            self.moves_list = moves_list
            self.children = []
            self.visited = False

        def add_child(self, moves_list: List[Move]):
            child = ConstraintSolver.SolverSubsetNode(parent=self, moves_list=moves_list)
            self.children.append(child)

    class SubsetSolver:
        def __init__(self, parent_solver: 'ConstraintSolver', sources: List[object], wip_solution_state: List[object], unmapped_sources_bitset: BitSet, evaluator_class, indent_level: int, debugging):
            timer = parent_solver.timer_name_to_timer["SubsetInit"]
            timer.begin()

            # Store our parent solver, so that we can alert them when done.
            self._parent_solver = parent_solver

            # Store our indent level so that we can trace debug properly.
            self.indent_level = indent_level

            # Remember what type of debugging we're doing.
            self.debugging = debugging

            # Store our evaluator class, so that we can construct them appropriately.
            self._evaluator_class = evaluator_class

            # Create an evaluator for every unmapped source.
            self._source_index_to_evaluator = {}
            self._unmapped_sources_bitset = BitSet.copy_construct_from(unmapped_sources_bitset)
            unmapped_source_index = self._unmapped_sources_bitset.get_next_set_bit_index(0)
            while unmapped_source_index is not None:
                source = sources[unmapped_source_index]
                evaluator = self._evaluator_class.factory_constructor(unmapped_source_index, source)
                self._source_index_to_evaluator[unmapped_source_index] = evaluator

                unmapped_source_index = self._unmapped_sources_bitset.get_next_set_bit_index(unmapped_source_index + 1)

            # Keep a reference to the sources (we won't alter these)
            self._sources = sources

            # Create a deep copy of our WIP solution state, as we *will* be altering that.
            self._wip_solution_state = copy.deepcopy(wip_solution_state)

            # Flag all of our destination nodes as dirty.
            self._dirty_destination_indices_bitset = BitSet(len(wip_solution_state))
            self._dirty_destination_indices_bitset.set_all()

            # Track which of the destinations are flagged as "empty" (those without 
            # anything assigned to them).  
            # We do this so that we don't do a ton of comparisons against each and 
            # every empty destination, when the results will be exactly the same.
            # We'll keep the first such one in the set, but all subsequent ones
            # won't be considered.
            self._empty_destinations_bitset = BitSet(len(wip_solution_state))
            first_empty_already_found = False
            for dest_index in range(len(wip_solution_state)):
                destination = wip_solution_state[dest_index]
                if self._evaluator_class.is_destination_empty(destination):
                    self._empty_destinations_bitset.set_bit(dest_index)

                    if first_empty_already_found == False:
                        first_empty_already_found = True
                    else:
                        # Clear out the dirty flag so that *this* empty isn't considered fair game
                        self._dirty_destination_indices_bitset.clear_bit(dest_index)

            timer.end()

        def assess_moves(self):
            # If no unmapped sources remain, flag success
            if len(self._source_index_to_evaluator.values()) == 0:
                # We're done, successfully!

                raise ConstraintSolver.AllItemsMappedSuccessfully()

            timer = self._parent_solver.timer_name_to_timer["AssessMoves"]
            timer.begin()

            # If we have dirty destinations, update each node to alert them.
            next_dirty_destination_index = self._dirty_destination_indices_bitset.get_next_set_bit_index(0)
            while next_dirty_destination_index is not None:
                destination = self._wip_solution_state[next_dirty_destination_index]

                for evaluator in self._source_index_to_evaluator.values():
                    evaluator.update_moves_for_destination(next_dirty_destination_index, destination)

                # We're no longer dirty.
                self._dirty_destination_indices_bitset.clear_bit(next_dirty_destination_index)

                # On to the next...
                next_dirty_destination_index = self._dirty_destination_indices_bitset.get_next_set_bit_index(next_dirty_destination_index + 1)

            timer.end()

        def choose_next_moves(self):
            # Find the edge(s) with the best scores.
            best_score = math.inf
            best_moves = []

            for evaluator in self._source_index_to_evaluator.values():
                timer = self._parent_solver.timer_name_to_timer["GetBestMoves"]
                timer.begin()

                score_moves_tuple = evaluator.get_list_of_best_moves()

                timer.end()

                score = score_moves_tuple[0]
                moves = score_moves_tuple[1]

                if len(moves) == 0:
                    # No moves?  We've failed.

                    # Emit debugging.
                    if self.debugging is not None:
                        indent_str = self.indent_level * '\t'
                        print(f"{indent_str}{self.__hash__()}: FAILED.  No moves available.")

                    raise ConstraintSolver.SolverFailed_NoMovesAvailableError()

                if score < best_score:
                    # Replace our previous best
                    best_score = score
                    best_moves = moves
                elif score == best_score:
                    # Append these moves
                    for move in moves:
                        best_moves.append(move)

            if best_score == -math.inf:
                # SPECIAL CASE:  These moves are free.  Take them all now.
                self._parent_solver._append_moves(self, [best_moves])
            else:
                # Otherwise, fork the state for other possibilities.
                child_move_lists = []
                for move in best_moves:
                    child_move_list = [move]
                    child_move_lists.append(child_move_list)

                self._parent_solver._append_moves(self, child_move_lists)

            # Increment our indent level
            self.indent_level = self.indent_level + 1

        def _execute_move(self, move: Move):
            timer = self._parent_solver.timer_name_to_timer["ExecuteMove"]
            timer.begin()

            # Emit debugging.
            if self.debugging is not None:
                indent_str = self.indent_level * '\t'
                print(f"{indent_str}{self.__hash__()}: Move {move.source_index} to {move.dest_index}.")

            # Apply it
            source_index = move.source_index
            evaluator = self._source_index_to_evaluator[source_index]
            source = evaluator.source

            dest_index = move.dest_index
            destination = self._wip_solution_state[dest_index]

            change_list = move.change_list

            # Call the static function to apply.
            self._evaluator_class.apply_changes(source, destination, change_list)

            # Remove the source evaluator, as we are now mapped.
            del self._source_index_to_evaluator[move.source_index]
            self._unmapped_sources_bitset.clear_bit(move.source_index)

            # Flag that this destination is now dirty.
            self._dirty_destination_indices_bitset.set_bit(dest_index)

            # If this index was once an empty, flag a new one as the available one.
            # Remember:  we only ever want ONE empty at any given time.
            if self._empty_destinations_bitset.is_set(dest_index):
                # Clear current one, but ONLY if we've verified that it is no longer empty
                # (we don't allow moves that leave a destination empty, as that could lead
                # to a source being improperly mapped to a dest).
                if self._evaluator_class.is_destination_empty(destination):
                    raise Exception("Destination was left empty after a move, which may lead to incorrect assignment.")
                else:
                    # Destination is actually NOT empty any longer.
                    self._empty_destinations_bitset.clear_bit(dest_index)

                    # Can we find another one?
                    next_empty = self._empty_destinations_bitset.get_next_set_bit_index(dest_index + 1)
                    if next_empty is not None:
                        # Mark it as dirty so that we can evaluate it as a possible move destination.
                        self._dirty_destination_indices_bitset.set_bit(next_empty)

            timer.end()