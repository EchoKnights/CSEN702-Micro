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


general_registers = {}
for i in range(32):
    general_registers[f"R({i})"] = [0]
    
floating_point_registers = {}
for i in range(32):
    floating_point_registers[f"F({i})"] = [0.0]
    floating_point_registers[f"F({i})_Qi"] = ['0']
    
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
    
def initialize_reservation_stations(a=3, fa=3, m=2, fm=2, l=3, s=3):
    global adder_reservation_stations, fp_adder_reservation_stations
    global mult_reservation_stations, fp_mult_reservation_stations
    global load_buffers, store_buffers
    
    for i in range(a):
        adder_reservation_stations[f"A{i+1}_time"] = [0]
        adder_reservation_stations[f"A{i+1}"+"_busy"] = [0]
        adder_reservation_stations[f"A{i+1}_op"] = [0]
        adder_reservation_stations[f"A{i+1}"+"_Vj"] = [0]
        adder_reservation_stations[f"A{i+1}"+"_Vk"] = [0]
        adder_reservation_stations[f"A{i+1}"+"_Qj"] = [""]
        adder_reservation_stations[f"A{i+1}"+"_Qk"] = [""]
        adder_reservation_stations[f"A{i+1}"+"_A"] = [""]        
        
    for i in range(fa):
        fp_adder_reservation_stations[f"FA{i+1}_time"] = [0]
        fp_adder_reservation_stations[f"FA{i+1}_busy"] = [0]
        fp_adder_reservation_stations[f"FA{i+1}_op"] = [0]
        fp_adder_reservation_stations[f"FA{i+1}_Vj"] = [0.0]
        fp_adder_reservation_stations[f"FA{i+1}_Vk"] = [0.0]
        fp_adder_reservation_stations[f"FA{i+1}_Qj"] = [""]
        fp_adder_reservation_stations[f"FA{i+1}_Qk"] = [""]
        fp_adder_reservation_stations[f"FA{i+1}_A"] = [""]        
        
    for i in range(m):
        mult_reservation_stations[f"M{i+1}_time"] = [0]
        mult_reservation_stations[f"M{i+1}_busy"] = [0]
        mult_reservation_stations[f"M{i+1}_op"] = [0]
        mult_reservation_stations[f"M{i+1}_Vj"] = [0]
        mult_reservation_stations[f"M{i+1}_Vk"] = [0]
        mult_reservation_stations[f"M{i+1}_Qj"] = [""]
        mult_reservation_stations[f"M{i+1}_Qk"] = [""]
        mult_reservation_stations[f"M{i+1}_A"] = [""]        
        
    for i in range(fm):
        fp_mult_reservation_stations[f"FM{i+1}_time"] = [0]
        fp_mult_reservation_stations[f"FM{i+1}"] = [0]
        fp_mult_reservation_stations[f"FM{i+1}_busy"] = [0]
        fp_mult_reservation_stations[f"FM{i+1}_op"] = [0.0]
        fp_mult_reservation_stations[f"FM{i+1}_Vj"] = [0.0]
        fp_mult_reservation_stations[f"FM{i+1}_Vk"] = [0.0]
        fp_mult_reservation_stations[f"FM{i+1}_Qj"] = [""]
        fp_mult_reservation_stations[f"FM{i+1}_Qk"] = [""]
        fp_mult_reservation_stations[f"FM{i+1}_A"] = [""]
        
    for i in range(l):
        load_buffers[f"L{i+1}_busy"] = [0]
        load_buffers[f"L{i+1}_address"] = [""]
        
    for i in range(s):
        store_buffers[f"S{i+1}_busy"] = [0]
        store_buffers[f"S{i+1}_address"] = [""]
        store_buffers[f"S{i+1}_v"] = [0.0]
        store_buffers[f"S{i+1}_Q"] = [""]
    
def initialize_simulator(instruction_file_path):
    instructions = open_instruction_file(instruction_file_path)
    load_instruction_memory(instructions)
    initialize_data_memory()
    
    print("Simulator initialized.")
    
def initialize_clock_cycle():
    global clock_cycle
    clock_cycle = 0
        