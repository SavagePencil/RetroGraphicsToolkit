import math
import copy
from ColorEntry import ColorEntry
from Bitset import BitSet
from FSM import FSM, State

class Move:
    def __init__(self, source_node_index, dest_node_index, change_list):
        self.source_node_index = source_node_index
        self.dest_node_index = dest_node_index
        self.change_list = change_list


class GraphSolver:
    def __init__(self, source_node_set, dest_node_set, evaluator_class):
        self._wip_instances_list = []
        
        # Create our first instance.
        committed_moves_list = []
        instance = GraphSolverInstance(self, source_node_set, dest_node_set, committed_moves_list, evaluator_class)
        self._wip_instances_list.append(instance)

        # Track successful instances
        self._successful_move_sequences = []

    def update(self):
        if len(self._wip_instances_list) > 0:
            instance = self._wip_instances_list[0]
            instance.update()

    def is_done(self):
        return len(self._wip_instances_list) == 0

    def get_solutions(self):
        if False == self.is_done():
            raise Exception("Attempted to get solutions when the solver was not finished!")
        else:
            return self._successful_move_sequences

    def add_instance(self, instance):
        self._wip_instances_list.append(instance)

    def instance_completed_successfully(self, instance, committed_moves):
        self._successful_move_sequences.append(committed_moves)

        # Remove from the WIP list.
        self._wip_instances_list.remove(instance)

    def instance_completed_unsuccessfully(self, instance):
        # Remove from the WIP list.
        self._wip_instances_list.remove(instance)


class GraphSolverInstance:
    def __init__(self, parent_solver, source_node_list, dest_node_list, committed_moves_list, evaluator_class):
        self._parent_solver = parent_solver
        
        self._evaluator_class = evaluator_class        

        # Start with a *copy* of the current moves
        self._committed_moves_list = committed_moves_list.copy()

        # Make a *reference* to the source node list, since it never changes.
        self._source_node_list = source_node_list

        # Start with all source nodes flagged as uncommitted
        num_source_nodes = len(self._source_node_list)
        self._uncommitted_source_node_bitset = BitSet(num_source_nodes)
        self._uncommitted_source_node_bitset.set_all()

        # ...except those that have committed moves
        for committed_move in self._committed_moves_list:
            source_node_index = committed_move.source_node_index
            self._uncommitted_source_node_bitset.clear_bit(source_node_index)

        # Make a *copy* of the destination node list, as this *will* change.
        self._dest_node_list = []
        for dest_node in dest_node_list:
            node = copy.deepcopy(dest_node)
            self._dest_node_list.append(node)

        # Start with all dest nodes as dirty
        num_dest_nodes = len(self._dest_node_list)
        self._dirty_dest_node_indices_set = BitSet(num_dest_nodes)
        self._dirty_dest_node_indices_set.set_all()

        # Start with assumption that all source nodes can *potentially* go to the dest nodes
        # (this will be cleared up after our dirty nodes get checked)
        self._src_to_dest_adjacency_matrix = []
        rows = num_source_nodes
        while rows > 0:
            adjacency_row = BitSet(num_dest_nodes)
            adjacency_row.set_all()
            self._src_to_dest_adjacency_matrix.append(adjacency_row)
            rows = rows - 1

        # Start with no potential moves; this will be fixed with first dirty pass.
        self._src_dest_to_potential_moves = {}

        # Start our machine off.
        self._fsm = FSM(self)
        self._fsm.start(GraphSolverInstance.TestForSuccessState)

    def execute_move(self, move):
        source_node_index = move.source_node_index

        # Commit to the move
        self._uncommitted_source_node_bitset.clear_bit(source_node_index)
        self._committed_moves_list.append(move)

        # Execute the move
        self._evaluator_class.execute_move(move, self._source_node_list, self._dest_node_list)

    def update(self):
        self._fsm.update()

    def _clear_adjacency(self, source_node_index):
        # Remove all potential moves related to this source node
        adjacency_row = self._src_to_dest_adjacency_matrix[source_node_index]
        next_adjacent_dest_index = adjacency_row.get_next_set_bit_index(0)
        while next_adjacent_dest_index is not None:
            move_key = (source_node_index, next_adjacent_dest_index)
            del self._src_dest_to_potential_moves[move_key]
            next_adjacent_dest_index = adjacency_row.get_next_set_bit_index(next_adjacent_dest_index + 1)

        adjacency_row.clear_all()

    class TestForSuccessState(State):
        @staticmethod
        def on_update(context):
            # If all nodes are committed, we are done.
            if context._uncommitted_source_node_bitset.are_all_clear():
                # We've completed successfully.
                return GraphSolverInstance.CompletedSuccessfullyState
            
            # Otherwise, we're still in it.  Transition to finding potential moves.
            return GraphSolverInstance.UpdatePossibleMovesState

    class CompletedSuccessfullyState(State):
        @staticmethod
        def on_enter(context):
            context._parent_solver.instance_completed_successfully(context, context._committed_moves_list)
            return None

    class CompletedFailureState(State):
        @staticmethod
        def on_enter(context):
            context._parent_solver.instance_completed_unsuccessfully(context)
            return None

    class UpdatePossibleMovesState(State):
        @staticmethod
        def on_update(context):
            # Update for dirty nodes.
            dirty_node_index = context._dirty_dest_node_indices_set.get_next_set_bit_index(0)
            while dirty_node_index is not None:
                dirty_node = context._dest_node_list[dirty_node_index]

                # Compare this dirty node against all uncommitted source nodes.
                uncommitted_node_index = context._uncommitted_source_node_bitset.get_next_set_bit_index(0)

                while uncommitted_node_index is not None:
                    # Make sure we haven't already ruled this one out.
                    adjacency_row = context._src_to_dest_adjacency_matrix[uncommitted_node_index]
                    if adjacency_row.is_set(dirty_node_index):
                        # We're potentially adjacent, so now check it out.
                        uncommitted_node = context._source_node_list[uncommitted_node_index]
                        changes = context._evaluator_class.get_changes_for_move(uncommitted_node, dirty_node)
                        if changes is None:
                            # CANNOT FIT.
                            # Rule it out on our adjacency matrix.
                            adjacency_row.clear_bit(dirty_node_index)

                            # Remove it from the potential moves list, if it was in there.
                            move_key = (uncommitted_node_index, dirty_node_index)
                            if move_key in context._src_dest_to_potential_moves:
                                del context._src_dest_to_potential_moves[move_key]
                        else:
                            # CAN FIT.
                            move_key = (uncommitted_node_index, dirty_node_index)
                            move = Move(uncommitted_node_index, dirty_node_index, changes)
                            context._src_dest_to_potential_moves[move_key] = move
                    
                    # If there are NO moves for this node, that means we've failed:  no path to a destination.
                    if adjacency_row.are_all_clear():
                        return GraphSolverInstance.CompletedFailureState

                    # Try next uncommitted.
                    uncommitted_node_index = context._uncommitted_source_node_bitset.get_next_set_bit_index(uncommitted_node_index + 1)

                # Try next dirty
                dirty_node_index = context._dirty_dest_node_indices_set.get_next_set_bit_index(dirty_node_index + 1)
            
            # No more dirties.
            context._dirty_dest_node_indices_set.clear_all()

            # Do we have ANY moves?  If not, this can't fit.
            if len(context._src_dest_to_potential_moves) == 0:
                return GraphSolverInstance.CompletedFailureState

            # Go pick some good moves.
            return GraphSolverInstance.ChooseNextMoveState

    class ChooseNextMoveState(State):
        @staticmethod
        def on_update(context):
            # Find the best move(s)
            best_score = math.inf
            best_moves = []

            for move in context._src_dest_to_potential_moves.values():
                source_node_index = move.source_node_index
                adjacency_row = context._src_to_dest_adjacency_matrix[source_node_index]
                score = context._evaluator_class.get_score_for_move(move, adjacency_row)
                if score < best_score:
                    # A new best!
                    best_score = score
                    best_moves.clear()
                    best_moves.append(move)
                elif score == best_score:
                    # Equally good!
                    best_moves.append(move)

            # We've evaluated all of the potential moves.  Select the best one(s).
            if best_score == -math.inf:
                # Special case for "free" moves:  we can do them *all at once*
                for free_move in best_moves:
                    context.execute_move(free_move)

                    # Remove the moved node and all its edges from the adjacency matrix.
                    context._clear_adjacency(free_move.source_node_index)
            else:
                # Take only one potential move.  We'll make the rest separate solver instances.
                best_move = best_moves.pop()
                for other_move in best_moves:
                    # Create another instance so that we can fork our decisions.
                    new_instance = GraphSolverInstance(context._parent_solver
                        , context._source_node_list
                        , context._dest_node_list
                        , context._committed_moves_list
                        , context._evaluator_class)
            
                    # Execute the new move on the instance.
                    new_instance.execute_move(other_move)

                    # Let the parent solver know about it so that it can schedule it when this one is complete.
                    context._parent_solver.add_instance(new_instance)

                # Mark the destination as dirty.
                context._dirty_dest_node_indices_set.set_bit(best_move.dest_node_index)

                # Execute the move
                context.execute_move(best_move)

                # Remove the moved node and all its edges from the adjacency matrix.
                context._clear_adjacency(best_move.source_node_index)

                return GraphSolverInstance.TestForSuccessState


