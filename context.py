class RegistrationStation:
    def __init__(self):
        self.Tag = None
        self.busy = False
        self.busy_time = 0
        self.opcode = ""
    
class LoadBuffer(RegistrationStation):
    total_load_buffers = 2
    busy_load_buffers = 0
    
    def __init__(self):
        super().__init__()
        self.address = 0
        
class StoreBuffer(RegistrationStation):
    total_store_buffers = 3
    busy_store_buffers = 0
    
    def __init__(self):
        super().__init__()
        self.address = 0
        self.V = 0
        self.Q = None
        
class AdditionBuffer(RegistrationStation):
    total_addition_buffers = 3
    busy_addition_buffers = 0
    
    def __init__(self):
        super().__init__()
        self.Vj = 0
        self.Vk = 0
        self.Qj = None
        self.Qk = None
        self.A = 0

class MultiplicationBuffer(RegistrationStation):
    total_multiplication_buffers = 2
    busy_multiplication_buffers = 0
    
    def __init__(self):
        super().__init__()
        self.Vj = 0
        self.Vk = 0
        self.Qj = None
        self.Qk = None
        self.A = 0
        
class FPAdditionBuffer(RegistrationStation):
    total_fp_addition_buffers = 3
    busy_fp_addition_buffers = 0
    
    def __init__(self):
        super().__init__()
        self.Vj = 0.0
        self.Vk = 0.0
        self.Qj = None
        self.Qk = None
        self.A = 0.0
        
class FPMultiplicationBuffer(RegistrationStation):
    total_fp_multiplication_buffers = 2
    busy_fp_multiplication_buffers = 0
    
    def __init__(self):
        super().__init__()
        self.Vj = 0.0
        self.Vk = 0.0
        self.Qj = None
        self.Qk = None
        self.A = 0.0
        
class GeneralRegister:
    total_general_registers = 32
    
    def __init__(self):
        self.value = 0
        self.Qi = None
    
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


pc = 0
clock_cycle = 0
single_word_size = 4
double_word_size = 8
cache_size = 16
block_size = 4
cache_lines = cache_size // block_size
cache_hit_latency = 1
cache_miss_penalty = 10

instruction_memory = []
data_memory = []

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
    
def increment_pc(value):
    global pc
    pc += value