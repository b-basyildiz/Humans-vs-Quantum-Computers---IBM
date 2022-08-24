from numpy.linalg import norm #vector norm
from numpy import array

#
def cost_function(current_state,optimal_state, bot_indices):
    """
    This function takes in a current game state and optimal game state as bitstrings, and finds 
    which move the computer should make (flipping one of the bits). The 'best' move is the bitstring
    that is closest to the optimal state. If there are mutliple optimal states, the first one is picked. 
    """
    #Finding all possible moves
    possible_states = []
    for i in range(len(current_state)):
        if i in bot_indices:
            temp_state = [bit for bit in current_state]
            if current_state[i] == 1:
                temp_state[i] = 0
            elif current_state[i]  == 0:
                temp_state[i] = 1
            else:
                raise Exception('Error: Bits must be 0 or 1')
            print(temp_state)
            possible_states.append(array(temp_state))
    
    #Finding best move 
    #We need to fix this 
    optimal_state = array(optimal_state)
    min = norm(optimal_state - possible_states[0])
    min_state = possible_states[0]
    for state in possible_states:
        if norm(optimal_state - state) < min:
            min = norm(current_state - state)
            min_state = state
    return min_state 

        
