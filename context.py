import numpy

isa = {
    'LW': 1,
    'LD': 2,
    'L.W': 3,
    'L.D': 4,
    'L. W': 3,
    'L. D': 4,
    'SW': 5,
    'SD': 6,
    'S.W': 7,
    'S.D': 8,
    'S. W': 7,
    'S. D': 8,
    
    'ADD': 9,
    'DADDI': 10,
    'SUB': 11,
    'DSUBI': 12,
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
    'ADD. D': 15,
    'ADD. S': 16,
    'SUB. D': 17,
    'SUB. S': 18,
    'MUL. D': 19,
    'MUL. S': 20,
    'DIV. D': 21,
    'DIV. S': 22,
    
    'J': 23,
    'JR': 24,
    'JAL': 25,
    'BEQ': 26,
    'BNE': 27,
    
    'NOP': 0
}

instruction_stats = []

pc = 0
clock_cycle = 0
single_word_size = 4
double_word_size = 8
cache_size = 64
block_size = 8
cache_lines = cache_size // block_size
cache_hit_latency = 1
cache_miss_penalty = 10
data_memory_size = 4096

fp_add_latency = 2
fp_mult_latency = 10
fp_div_latency = 40
load_latency = 2
store_latency = 2
add_latency = 1

instruction_memory = []
data_memory = []
cache = {}

ADDRESS_WIDTH = 32

address_size = ADDRESS_WIDTH

cache_lines = cache_size // block_size
index = int(numpy.log2(cache_lines))
block_offset = int(numpy.log2(block_size))
valid_bit = 0
tag = address_size - (index + block_offset)

rs = 0
rt = 0
rd = 0
immediate = 0
address = 0
name = ""

val_rs = 0
val_rt = 0

CDB = {
    "tag": None,
    "value": None,
}

STALL = False

# ------------------------------------------------------------------- #

g, f = 32, 32

general_registers = {}    
floating_point_registers = {}

for i in range(g):
    general_registers[f"R{i}"] = {
        "Value": 0.0,
        "Qi": "0",
}
for i in range(f):
    floating_point_registers[f"F{i}"] = {
        "Value": 0.0,
        "Qi": "0",
}

adder_reservation_stations = {}
fp_adder_reservation_stations = {}
mult_reservation_stations = {}
fp_mult_reservation_stations = {}
load_buffers = {}
store_buffers = {}

# ------------------------------------------------------------------- #

# initialization functions

def open_instruction_file(file_path):
    with open(file_path, 'r') as file:
        instructions = [line.strip() for line in file if line.strip()]
    return instructions

def initialize_data_memory(data_memory_size=4096, cache_size=64, block_size=8):
    global data_memory
    global cache
    
    data_memory = ['00000000'] * data_memory_size
    
    cache_lines = cache_size // block_size
    cache = {}
    for i in range(cache_lines):
        cache[i] = {
            'Set': i,
            "valid": 0,
            "tag": None,
            "data": ['00000000'] * block_size
        }
        
    
    print(f"Data memory initialized: {data_memory_size} bytes")
    print(f"Cache configuration: {cache_size} bytes, {block_size} bytes per block")
    print(f"Number of cache blocks: {cache_size // block_size}")

def load_instruction_memory(instructions):
    global instruction_memory

    instruction_memory = instructions
    
def initialize_reservation_stations(g = 32, f= 32, a=3, fa=3, m=2, fm=2, l=3, s=3):
    global adder_reservation_stations, fp_adder_reservation_stations
    global mult_reservation_stations, fp_mult_reservation_stations
    global load_buffers, store_buffers
    global floating_point_registers, general_registers
    
    for i in range(a):
        name = f"A{i+1}"

        adder_reservation_stations[name] = {
            "time": 0,
            "busy": 0,
            "op": None,
            "Vj": 0,
            "Vk": 0,
            "Qj": "0",
            "Qk": "0",
            "A":  "",
        }  
        
    for i in range(fa):
        name = f"FA{i+1}"

        fp_adder_reservation_stations[name] = {
            "time": 0,
            "busy": 0,
            "op": None,
            "Vj": 0.0,
            "Vk": 0.0,
            "Qj": "0",
            "Qk": "0",
            "A":  "",
        }
        
    for i in range(m):
        name = f"M{i+1}"

        mult_reservation_stations[name] = {
            "time": 0,
            "busy": 0,
            "op": None,
            "Vj": 0,
            "Vk": 0,
            "Qj": "0",
            "Qk": "0",
            "A":  "",        
        }
        
    for i in range(fm):
        name = f"FM{i+1}"

        fp_mult_reservation_stations[name] = {
            "time": 0,
            "busy": 0,
            "op": None,
            "Vj": 0.0,
            "Vk": 0.0,
            "Qj": "0",
            "Qk": "0",
            "A":  "",
        }
        
    for i in range(l):
        name = f"L{i+1}"
        
        load_buffers[name] = {
            'time': 0,
            "busy": 0,
            "op": None,
            "Vj": 0.0,
            "Vk": 0.0,
            "Qj": "0",
            "Qk": "0",
            "A":  "",
        }
        
    for i in range(s):
        name = f"S{i+1}"
        
        store_buffers[name] = {
            'time': 0,
            "busy": 0,
            "op": None,
            "Vj": 0.0,
            "Vk": 0.0,
            "Qj": "0",
            "Qk": "0",
            "A":  "",
        }
        
def initialize_clock_cycle():
    global clock_cycle
    clock_cycle = 0
    
def initialize_program_counter():
    global pc
    pc = 0
    
def increment_pc(offset):
    global pc
    pc += offset
    
def initialize_simulator(instruction_file_path):
    instructions = open_instruction_file(instruction_file_path)
    load_instruction_memory(instructions)
    initialize_data_memory()
    initialize_clock_cycle()
    initialize_program_counter()
    initialize_reservation_stations()
    
    print("Simulator initialized.")

        
def stall_pipeline():
    global STALL
    STALL = True
    print("Pipeline stalled.")
    
def unstall_pipeline():
    global STALL
    STALL = False
    print("Pipeline unstalled.")
    