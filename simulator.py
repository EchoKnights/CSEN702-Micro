clock_cycles = 0
instruction_memory = []
data_memory = []

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
    'BEQ': 26,
    'BNE': 27,
    
    'NOP': 0
}

# ------------------------------------------------------------------- #

# initialization functions

def open_instruction_file(file_path):
    with open(file_path, 'r') as file:
        instructions = [line.strip() for line in file if line.strip()]
    return instructions

def decode_instruction(instruction):
    parts = instruction.split()
    opcode = parts[0]
    operands = parts[1:] if len(parts) > 1 else []
    return opcode, operands

def load_instruction_memory(instructions):
    global instruction_memory
    instruction_memory = instructions[:]
    
# ------------------------------------------------------------------- #

# logic functions

def reset_simulator():
    global clock_cycles, instruction_memory, data_memory
    clock_cycles = 0
    instruction_memory = []
    data_memory = []

def increment_clock_cycles(cycles):
    global clock_cycles
    clock_cycles += cycles
    
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
    