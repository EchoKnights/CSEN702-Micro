import context
import fetch

            
def execute_instruction(name, station):
    if name[0] == 'F':
        if (name[1] == 'A') or (name[1] == 'M'):
            print (f"Executing FP instruction at station {name}")

            
            if (station['Qj'] in (0, '0')):
                print(station['Qj'])
                print(1)
                res_1 = station['Vj']
            else: 
                print(station['Qj'])
                print(2)
                res_1 = station['Qj']
            if (station['Qk'] in (0, '0')):
                print(station['Qk'])
                print(1)
                res_2 = station['Vk']
            else:
                print(station['Qk'])
                print(2)
                res_2 = station['Qk']
            result = execute_fp_arithmatic(station['op'], res_1, res_2)
            print(f"Executed FP instruction at station {name}, result: {result}")
            return result
    elif name[0] == 'L':
        return fetch.pull_value_from_register(station['address'])
    elif name[0] == 'S':
        if (station['Q'] in (0, '0')):
            value = station['V']
        else:
            value = station['Q']
        address = station['address']
        fetch.set_in_register(address, 0, value)
        return 1
    else:
        return execute_integer_arithmatic()
    
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
    
def execute_integer_arithmatic():
    return