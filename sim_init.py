pc = 0
clock_cycles = 0
single_word_size = 4
double_word_size = 8
cache_size = 16
block_size = 4
cache_lines = cache_size // block_size
cache_hit_latency = 1
cache_miss_penalty = 10

tag = 0
index = 0
offset = 0
valid_bit = 0

rs = 0
rt = 0
rd = 0
immediate = 0
address = 0
name = ""

val_rs = 0
val_rt = 0

general_registers = { f'R{i}': 0 for i in range(32) }
instruction_memory = []
cache = [ {'tag': None, 'data': [0]*block_size, 'valid': False} for _ in range(cache_lines) ]
data_memory = []
stages = {
    'IF': 'Instruction Fetch',
    'ID': 'Instruction Decode',
    'EX': 'Execute',
    'MEM': 'Memory Access',
    'WB': 'Write Back'
}
if_id_register = []
id_ex_register = [pc, {"Opcode": None, "RS Value": val_rs, "RT Value": val_rt, "Immediate": immediate, "Address": address, "Name": name, "Valid Bit": valid_bit}]
ex_mem_register = []
mem_wb_register = []

isa = {
    'LW': 1,
    'LD': 2,
    'L.W': 3,
    'L.D': 4,
    'SW': 5,
    'SD': 6,
    'S.W': 7,
    'S.D': 8,
    
    'ADD': 9,
    'ADDI': 10,
    'SUB': 11,
    'SUBI': 12,
    'MUL': 13,
    'DIV': 14,
    
    'ADD.D': 15,
    'ADD.S': 16,
    'SUB.D': 17,
    'SUB.S': 18,
    'MUL.D': 19,
    'MUL.S': 20,
    'DIV.D': 21,
    'DIV.S': 22,
    
    'J': 23,
    'JR': 24,
    'JAL': 25,
    'BEQZ': 26,
    'BNE': 27,
    
    'NOP': 0
}

# ------------------------------------------------------------------- #

# initialization functions

def open_instruction_file(file_path):
    with open(file_path, 'r') as file:
        instructions = [line.strip() for line in file if line.strip()]
    return instructions

def initialize_data_memory(size=None):
    global data_memory
    if size is None:
        num_cache_blocks = cache_size // block_size
        memory_blocks = num_cache_blocks * 16
        size = memory_blocks * block_size
    
    data_memory = [0] * size
    print(f"Data memory initialized: {size} bytes")
    print(f"Cache configuration: {cache_size} bytes, {block_size} bytes per block")
    print(f"Number of cache blocks: {cache_size // block_size}")

def load_instruction_memory(instructions):
    global instruction_memory
    instruction_memory = instructions[:]
    
def initialize_simulator(instruction_file_path):
    instructions = open_instruction_file(instruction_file_path)
    load_instruction_memory(instructions)
    initialize_data_memory()
    
    print("Simulator initialized.")
    