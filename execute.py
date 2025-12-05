import context
import fetch
import cache

            
def execute_instruction(name, station):
    address = 0
    if name[0] == 'F':
        if (name[1] == 'A') or (name[1] == 'M'):
            print (f"Executing FP instruction at station {name}")
            if station['Qj'] not in (0, '0'):
                print(f"Warning: FP instruction at {name} executed but Qj={station['Qj']} is not ready")
                return 0
            if station['Qk'] not in (0, '0'):
                print(f"Warning: FP instruction at {name} executed but Qk={station['Qk']} is not ready")
                return 0
            
            try:
                res_1 = float(station['Vj']) if station['Vj'] != '-' else 0
                res_2 = float(station['Vk']) if station['Vk'] != '-' else 0
                result = execute_fp_arithmatic(station['op'], res_1, res_2)
                print(f"Executed FP instruction at station {name}, result: {result}")
                return result
            except (ValueError, TypeError, KeyError) as e:
                print(f"Error in FP instruction execution: {e}")
                return 0
    elif name[0] == 'L':
        print (f'Executing Load instruction at station {name}')
        if station['Qj'] in (0, '0'):
            res_1 = station['Vj']
        else: 
            res_1 = station['Qj']
            
        try:
            base_addr = int(float(res_1)) if res_1 != '-' else 0
            offset = int(station['A']) if station['A'] != '' and station['A'] != '-' else 0
            address = base_addr + offset
            
            if address < 0 or address >= len(context.data_memory):
                print(f"Error: Invalid load address {address} (memory size: {len(context.data_memory)})")
                return 0
            
            num_bytes = 8 if station['op'] in (2, 4) else 4
            if address + num_bytes > len(context.data_memory):
                print(f"Error: Load would exceed memory bounds (address {address} + {num_bytes} bytes)")
                return 0
            
            if station['op'] in (2, 4):
                print(f'Load Double from address {address}')
                result = get_from_memory(address, 8)
            else:
                print(f'Load Single from address {address}')
                result = get_from_memory(address, 4)
            return result
        except (ValueError, TypeError, KeyError) as e:
            print(f"Error in load instruction execution: {e}")
            return 0
    elif name[0] == 'S':
        print (f'Executing Store instruction at station {name}')
        if station['Qj'] not in (0, '0'):
            print(f"Warning: Store instruction at {name} executed but Qj={station['Qj']} is not ready")
            return None
        if station['Qk'] not in (0, '0'):
            print(f"Warning: Store instruction at {name} executed but Qk={station['Qk']} is not ready")
            return None
        
        try:
            res_1 = float(station['Vj']) if station['Vj'] != '-' else 0  # Base address
            res_2 = float(station['Vk']) if station['Vk'] != '-' else 0  # Value to store
            
            base_addr = int(res_1) if res_1 != '-' else 0
            offset = int(station['A']) if station['A'] != '' and station['A'] != '-' else 0
            address = int(base_addr) + int(offset)
            
            if address < 0 or address >= len(context.data_memory):
                print(f"Error: Invalid store address {address} (memory size: {len(context.data_memory)})")
                return None
            
            num_bytes = 8 if station['op'] in (6, 8) else 4
            if address + num_bytes > len(context.data_memory):
                print(f"Error: Store would exceed memory bounds (address {address} + {num_bytes} bytes)")
                return None
            
            if station['op'] in (6, 8):
                print(f'Store Double to address {address}')
                write_to_memory(address, res_2, 8)
            else:
                print(f'Store Single to address {address}')
                write_to_memory(address, res_2, 4)
            return None  # Stores don't return a value
        except (ValueError, TypeError, KeyError) as e:
            print(f"Error in store instruction execution: {e}")
            return None
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
        if station['Qj'] not in (0, '0'):
            print(f"Warning: Integer instruction at {name} executed but Qj={station['Qj']} is not ready")
            return 0
        if station['Qk'] not in (0, '0'):
            print(f"Warning: Integer instruction at {name} executed but Qk={station['Qk']} is not ready")
            return 0
        
        try:
            res_1 = float(station['Vj']) if station['Vj'] != '-' else 0
            res_2 = float(station['Vk']) if station['Vk'] != '-' else 0
            immediate = station.get('A', '') or ''
            result = execute_integer_arithmatic(station['op'], res_1, res_2, immediate)
            print(f"Executed Integer instruction at station {name}, result: {result}")
            return result
        except (ValueError, TypeError, KeyError) as e:
            print(f"Error in Integer instruction execution: {e}")
            return 0
    
def execute_fp_arithmatic(op, rs, rt):
    try:
        rs_val = float(rs) if rs != '-' else 0
        rt_val = float(rt) if rt != '-' else 0
        
        if op == 15:  # ADD.D
            return rs_val + rt_val
        elif op == 16:  # ADD.S
            return rs_val + rt_val
        elif op == 17:  # SUB.D
            return rs_val - rt_val
        elif op == 18:  # SUB.S
            return rs_val - rt_val
        elif op == 19:  # MUL.D
            return rs_val * rt_val
        elif op == 20:  # MUL.S
            return rs_val * rt_val
        elif op == 21:  # DIV.D
            if rt_val == 0:
                print(f"Error: Division by zero in DIV.D operation")
                return 0
            return rs_val / rt_val
        elif op == 22:  # DIV.S
            if rt_val == 0:
                print(f"Error: Division by zero in DIV.S operation")
                return 0
            return rs_val / rt_val
    except (ValueError, TypeError) as e:
        print(f"Error in FP arithmetic: {e}")
        return 0
    
def execute_integer_arithmatic(op, rs, rt, immediate):
    try:
        rs_val = int(float(rs)) if rs != '-' else 0
        rt_val = int(float(rt)) if rt != '-' else 0
        imm_val = int(immediate) if immediate and immediate != '' else 0
        
        if op == 9:  # ADD
            return rs_val + rt_val
        elif op == 10:  # DADDI
            return rs_val + imm_val
        elif op == 11:  # SUB
            return rs_val - rt_val
        elif op == 12:  # DSUBI
            return rs_val - imm_val
        elif op == 13:  # MUL
            return rs_val * rt_val
        elif op == 14:  # DIV
            if rt_val == 0:
                print(f"Error: Division by zero in DIV operation")
                return 0
            return rs_val / rt_val
    except (ValueError, TypeError) as e:
        print(f"Error in integer arithmetic: {e}")
        return 0
    
    
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
    
def get_from_memory(address, size):
    """
    Load data from memory (via cache).
    Returns numeric value (int or float).
    """
    res = cache.search_cache(address, size)
    if res is None:
        cache.load_into_cache(address)
        res = cache.search_cache(address, size)
    
    if res is None:
        print(f"Error: Failed to load from address {address}")
        return 0
    
    if size == 4:
        value = int(res, 2)
        if value & 0x80000000:
            value = value - (1 << 32)
    else:
        value = int(res, 2)
        if value & 0x8000000000000000:
            value = value - (1 << 64)
    
    return value

def write_to_memory(address, value, num_bytes=4):
    """
    Write value to memory (via cache).
    value: numeric value to write
    num_bytes: number of bytes (4 for single, 8 for double)
    """
    cache.write_into_cache(address, value, num_bytes)
    return None