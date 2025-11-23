import sim_init
import id
    
# ------------------------------------------------------------------- #

# logic functions

def reset_simulator():
    global clock_cycles, instruction_memory, data_memory, pc
    pc = 0
    clock_cycles = 0
    instruction_memory = []
    data_memory = []
    print("Simulator reset.")
    
def pipeline_stages():
    print("Pipeline Stages:")
    for stage, description in sim_init.stages.items():
        print(f"{stage}: {description}")

def increment_clock_cycles(cycles):
    global clock_cycles
    clock_cycles += cycles
    print('-----------------------------------------')
    print(f'Clock Cycle: {clock_cycles}')
    
def increment_pc(amount):
    global pc
    pc += amount
    
def cache_access(address):
    print(f"Accessing cache for address: {address}")
    block_number = address // sim_init.block_size
    index = block_number % sim_init.cache_lines
    tag = block_number // sim_init.cache_lines
    offset = address % sim_init.block_size
    
    block = sim_init.cache[index]
    if block['valid'] and block['tag'] == tag:
        print("Cache hit")
        return block['data'][offset], True
    else:
        print("Cache miss")
        block_start_addr = block_number * sim_init.block_size
        block_data = sim_init.data_memory[block_start_addr:block_start_addr + sim_init.block_size]
        sim_init.cache[index]['tag'] = tag
        sim_init.cache[index]['data'] = block_data
        sim_init.cache[index]['valid'] = True
        return block_data[offset], False
    
    
# ------------------------------------------------------------------- #
    
# debug functions    
    
def print_instruction_memory():
    for idx, instruction in enumerate(instruction_memory):
        print(f"{idx}: {instruction}")
        
def print_data_memory():
    for idx, data in enumerate(data_memory):
        print(f"{idx}: {data}")
        
def print_clock_cycles():
    print(f"Total Clock Cycles: {clock_cycles}")
    
# ------------------------------------------------------------------- #

def main():
    print('Enter example instruction')
    instruction = input().strip()
    opcode, operands, rs, rt, rd, immediate, address, name, val_rs, val_rt = id.decode_instruction(instruction)
    print(f"Opcode: {opcode}, Operands: {operands}, RS: {rs}, RT: {rt}, RD: {rd}, Immediate: {immediate}, Address: {address}, Name: {name}")
    
if __name__ == "__main__":
    main()
