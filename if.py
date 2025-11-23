import sim_init
from simulator import increment_pc

def pull_next_instruction():
    if sim_init.pc < len(sim_init.instruction_memory):
        instruction = sim_init.instruction_memory[sim_init.pc]
        increment_pc(1)
        return instruction
    else:
        return None
    
def update_if_id_register(instruction):
    global if_id_register
    if_id_register = {
        'instruction': instruction
    }
    