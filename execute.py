import context
import fetch

            
def execute_instruction(name, station):
    address = 0
    if name[0] == 'F':
        if (name[1] == 'A') or (name[1] == 'M'):
            print (f"Executing FP instruction at station {name}")
            if (station['Qj'] in (0, '0')):
                res_1 = station['Vj']
            else: 
                res_1 = station['Qj']
            if (station['Qk'] in (0, '0')):
                res_2 = station['Vk']
            else:
                res_2 = station['Qk']
            result = execute_fp_arithmatic(station['op'], res_1, res_2)
            print(f"Executed FP instruction at station {name}, result: {result}")
            return result
    elif name[0] == 'L':
        print (f'Executing Load instruction at station {name}')
        if station['Qj'] in (0, '0'):
            res_1 = station['Vj']
        else: 
            res_1 = station['Qj']
            
        address = res_1 + station['A']
        result = fetch.get_from_memory(address)
        return result
    elif name[0] == 'S':
        print (f'Executing Store instruction at station {name}')
        if station['Qj'] in (0, '0'):
            res_1 = station['Vj']
        else: 
            res_1 = station['Qj']
            
        address = res_1 + station['A']
        value = None
        print(address)
        return fetch.write_to_memory(address, value)
    elif station['op'] in (26, 27):
        print (f"Executing Loop instruction at station {name}")
        if (station['Qj'] in (0, '0')):
            res_1 = station['Vj']
        else: 
            res_1 = station['Qj']
        if (station['Qk'] in (0, '0')):
            res_2 = station['Vk']
        else:
            res_2 = station['Qk']
        handle_loop_instruction(station['op'], res_1,  res_2, station['A'])
    else:
        print (f"Executing Integer instruction at station {name}")
        if (station['Qj'] in (0, '0')):
            res_1 = station['Vj']
        else: 
            res_1 = station['Qj']
        if (station['Qk'] in (0, '0')):
            res_2 = station['Vk']
        else:
            res_2 = station['Qk']
        result = execute_integer_arithmatic(station['op'], res_1, res_2, station['A'])
        print(f"Executed Integer instruction at station {name}, result: {result}")
        return result
    
def execute_fp_arithmatic(op, rs, rt):
    if op == 15:  # ADD.D
        return int(rs) + int(rt)
    elif op == 16:  # ADD.S
        return int(rs) + int(rt)
    elif op == 17:  # SUB.D
        return int(rs) - int(rt)
    elif op == 18:  # SUB.S
        return int(rs) - int(rt)
    elif op == 19:  # MUL.D
        return int(rs) * int(rt)
    elif op == 20:  # MUL.S
        return int(rs) * int(rt)
    elif op == 21:  # DIV.D
        return int(rs) / int(rt)
    elif op == 22:  # DIV.S
        return int(rs) / int(rt)
    
def execute_integer_arithmatic(op, rs, rt, immediate):
    if op == 9:  # ADD
        return int(rs) + int(rt)
    elif op == 10:  # DADDI
        return int(rs) + int(immediate)
    elif op == 11:  # SUB
        return int(rs) - int(rt)
    elif op == 12:  # DSUBI
        return int(rs) - int(immediate)
    elif op == 13:  # MUL
        return int(rs) * int(rt)
    elif op == 14:  # DIV
        return int(rs) / int(rt)
    
    
def handle_loop_instruction(opcode, rs_value, rt_value, name):
    new_pc = None
    new_pc = compute_loopback_address(name)
    do_loop = compute_if_loop(rs_value, rt_value, opcode)
    if do_loop is True:
        context.pc = new_pc
        print(f"Loop taken. New PC: {context.pc}")
        context.unstall_pipeline()
        return None
    else:
        print("Loop not taken.")
        context.increment_pc(1)
        context.unstall_pipeline()
        return 0

def compute_if_loop(rs_value, rt_value, opcode):
    if opcode == 26:  # BEQ
        return rs_value == rt_value
    elif opcode == 27:  # BNE
        return rs_value != rt_value
    return False

def compute_loopback_address(label):
    if label in fetch.labels:
        return fetch.labels[label]
    else:
        print(f"Error: Label '{label}' not found.")
        return 0