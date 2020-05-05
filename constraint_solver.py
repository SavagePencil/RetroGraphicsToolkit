import math
import copy
from BitSet import BitSet
from FSM import FSM, State

from ColorEntry import ColorEntry

class Move:
    def __init__(self, source_index, dest_index, change_list):
        self.source_index = source_index
        self.dest_index = dest_index
        self.change_list = change_list


class Evaluator:
    def __init__(self, source_index, source):
        self.source_index = source_index
        self.source = source
    
    def get_list_of_best_moves(self):
        pass

    def update_moves_for_destination(self, destination_index, destination):
        pass


class ConstraintSolver:
    def __init__(self, sources, destinations, evaluator_class):
        self.instances = []

        self.solutions = []

        committed_moves = []
        unmapped_sources_bitset = BitSet(len(sources))
        unmapped_sources_bitset.set_all()
        subset_solver = ConstraintSolver.SubsetSolver(self, sources, destinations, committed_moves, unmapped_sources_bitset, evaluator_class)
        self._wip_subset_solvers = []
        self._wip_subset_solvers.append(subset_solver)

        self._fsm = FSM(self)
        self._fsm.start(ConstraintSolver.AssessCompletionState)

    def is_complete(self):
        curr_state = self._fsm.get_current_state()
        if curr_state == ConstraintSolver.CompletedState:
            return True

        return False

    def update(self):
        self._fsm.update()

    def _add_subset_solver(self, subset_solver):
        # Append this to our current list.
        self._wip_subset_solvers.append(subset_solver)

    def _current_subset_solver_successful(self):
        subset_solver = self._wip_subset_solvers[0]
        new_solution = copy.deepcopy(subset_solver._committed_moves)
        self.solutions.append(new_solution)

        # Remove the current subset solver.
        self._wip_subset_solvers.pop(0)

    def _current_subset_solver_failed(self):
        # Remove the current subset solver.
        self._wip_subset_solvers.pop(0)

    class AssessCompletionState(State):
        @staticmethod
        def on_enter(context):
            if len(context._wip_subset_solvers) == 0:
                return ConstraintSolver.CompletedState
            return ConstraintSolver.AssessMovesState

    class AssessMovesState(State):
        @staticmethod
        def on_update(context):
            subset_solver = context._wip_subset_solvers[0]
            try:
                subset_solver.assess_moves()
            except ConstraintSolver.AllItemsMappedSuccessfully:
                return ConstraintSolver.SuccessfulSubsetCompletionState
            else:
                return ConstraintSolver.SelectMovesState

    class SelectMovesState(State):
        @staticmethod
        def on_update(context):
            subset_solver = context._wip_subset_solvers[0]
            try:
                subset_solver.choose_next_moves()
            except ConstraintSolver.SolverFailed_NoMovesAvailableError:
                return ConstraintSolver.FailedSubsetCompletionState
            else:
                return ConstraintSolver.AssessMovesState

    class SuccessfulSubsetCompletionState(State):
        @staticmethod
        def on_enter(context):
            # Add the current solver as a solution.
            context._current_subset_solver_successful()

            return ConstraintSolver.AssessCompletionState

    class FailedSubsetCompletionState(State):
        @staticmethod
        def on_enter(context):
            # Remove the current solver as failed.
            context._current_subset_solver_failed()

            return ConstraintSolver.AssessCompletionState

    class CompletedState(State):
        pass

    class AllItemsMappedSuccessfully(Exception):
        pass

    class SolverFailed_NoMovesAvailableError(Exception):
        pass

    class SubsetSolver:
        def __init__(self, parent_solver, sources, wip_solution_state, committed_moves, unmapped_sources_bitset, evaluator_class):
            # Store our parent solver, so that we can alert them when done.
            self._parent_solver = parent_solver

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

            # Create a copy of the committed moves (shallow is fine, as we aren't altering moves)
            self._committed_moves = copy.copy(committed_moves)

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

        def assess_moves(self):
            # If no unmapped sources remain, flag success
            if len(self._source_index_to_evaluator.values()) == 0:
                # We're done, successfully!
                raise ConstraintSolver.AllItemsMappedSuccessfully()

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

        def choose_next_moves(self):
            # Find the edge(s) with the best scores.
            best_score = math.inf
            best_moves = []

            for evaluator in self._source_index_to_evaluator.values():
                score_moves_tuple = evaluator.get_list_of_best_moves()

                score = score_moves_tuple[0]
                moves = score_moves_tuple[1]

                if len(moves) == 0:
                    # No moves?  We've failed.
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
                for move in best_moves:
                    self._execute_move(move)
            else:
                # Otherwise, fork the state for other possibilities.
                first_move = best_moves.pop()

                for alt_best_move in best_moves:
                    # Create alternate subsets to solve these.
                    subset = ConstraintSolver.SubsetSolver(self._parent_solver, self._sources, self._wip_solution_state, self._committed_moves, self._unmapped_sources_bitset, self._evaluator_class)

                    # Execute the move
                    subset._execute_move(alt_best_move)

                    # Add it to the solver to figure out.
                    self._parent_solver._add_subset_solver(subset)
                
                # Execute our own move on ourselves now.
                self._execute_move(first_move)

        def _execute_move(self, move):
            # Record it
            self._committed_moves.append(move)

            # Apply it
            source_index = move.source_index
            dest_index = move.dest_index
            change_list = move.change_list
            destination = self._wip_solution_state[dest_index]
            evaluator = self._source_index_to_evaluator[source_index]
            evaluator.apply_changes(destination, change_list)

            # Remove the source evaluator, as we are now mapped.
            del self._source_index_to_evaluator[move.source_index]
            self._unmapped_sources_bitset.clear_bit(move.source_index)

            # Flag that this destination is now dirty.
            self._dirty_destination_indices_bitset.set_bit(dest_index)

            # If this index was once an empty, flag a new one as the available one.
            # Remember:  we only ever want ONE empty at any given time.
            if self._empty_destinations_bitset.is_set(dest_index):
                # Clear current one.
                self._empty_destinations_bitset.set_bit(dest_index)

                # Can we find another one?
                next_empty = self._empty_destinations_bitset.get_next_set_bit_index(dest_index + 1)
                if next_empty is not None:
                    # Mark it as dirty so that we can evaluate it as a possible move destination.
                    self._dirty_destination_indices_bitset.set_bit(next_empty)