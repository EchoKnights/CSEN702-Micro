import context
import fetch
import execute


fetch.set_in_register('R1', 0, 10)
fetch.set_in_register('R2', 0, 20)
fetch.set_in_register('R10', 0, 77)

fetch.set_in_register('F1', 0, 5.5)
fetch.set_in_register('F2', 0, 2.0)
fetch.set_in_register('F3', 1, "A3")
context.initialize_reservation_stations()

def print_state():
    print('\n')
    print(f"State of Load buffers: {context.load_buffers}")
    print('\n')
    print(f"State of Store buffers: {context.store_buffers}")
    print('\n')
    print(f"State of floating adder reservation stations: {context.fp_adder_reservation_stations}")
    print ('\n')
    print(f'State of floating multiplier reservation stations: {context.fp_mult_reservation_stations}')
    print('\n')
    print(f"State of floating registers: {context.floating_point_registers}")
    print('\n')
    print(f"State of registers: {context.general_registers}")
    print('\n')


def increment_cycle():
    context.clock_cycle += 1
    
    print('----------------------------------------')
    print('\n')
    print(f"Cycle: {context.clock_cycle}")
    print('\n')
    print('----------------------------------------')
    print('\n')
    
def fetch_cycle():
    print('Input Instruction:')
    instruction = input().strip()
    if instruction == "":
        print("No instruction fetched.")
        return
    fetch.write_to_reservation_station(fetch.decode_instruction(instruction))
    
def execute_cycle():
    execute.execute_cycle()
    
while(True):
    fetch_cycle()
    print_state()
    
    increment_cycle()
    execute_cycle()
    print_state()
    