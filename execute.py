import context
import fetch

def iter_all_units():
    # FP adder stations
    for name, st in context.fp_adder_reservation_stations.items():
        yield name, st

    # FP mult/div stations
    for name, st in context.fp_mult_reservation_stations.items():
        yield name, st

    # Load buffers
    for name, st in context.load_buffers.items():
        yield name, st

    # Store buffers
    for name, st in context.store_buffers.items():
        yield name, st


def check_if_ready(station):
    qj = str(station.get('Qj', ''))
    qk = str(station.get('Qk', ''))
    
    print(f"Checking readiness: Qj={qj}, Qk={qk}")

    def _is_numeric(s):
        return s.isdigit() or (s.startswith('-') and s[1:].isdigit())

    if _is_numeric(qj) and _is_numeric(qk):
        print ("Instruction is ready to execute.")
        return True
    print ("Instruction is NOT ready to execute.")
    return False

def check_if_store_ready(station):
    q = str(station.get('Q', ''))

    def _is_numeric(s):
        return s.isdigit() or (s.startswith('-') and s[1:].isdigit())

    if _is_numeric(q):
        return True
    return False

def check_if_load_ready(station):
    address = str(station.get('address', ''))

    def _is_numeric(s):
        return s.isdigit() or (s.startswith('-') and s[1:].isdigit())

    if _is_numeric(address):
        return True
    return False

def execute_cycle():
    ready_to_execute = []

    for name, station in iter_all_units():
        if station.get("busy", 0) == 1 and station.get("time", 0) > 0:
            station["time"] -= 1
            if station["time"] == 0:
                ready_to_execute.append((name, station))

    for name, station in ready_to_execute:
        print('TEST:"', ready_to_execute)
        execute_instruction(name, station)

            
def execute_instruction(name, station):
    if name[0] == 'F':
        if not check_if_ready(station):
            return None
        if (name[1] == 'A') or (name[1] == 'M'):
            res_1 = station['Qj'] if station['Qj'] != 0 else station['Vj']
            res_2 = station['Qk'] if station['Qk'] != 0 else station['Vk']
            result = execute_fp_arithmatic(station['op'], res_1, res_2)
            print(f"Executed FP instruction at station {name}, result: {result}")
            return result
    elif name[0] == 'L':
        if not check_if_load_ready(station):
            return None
        return fetch.pull_value_from_register(station['address'])
    elif name[0] == 'S':
        if not check_if_store_ready(station):
            return None
        value = fetch.pull_value_from_register(station['Q'] if station['Q'] != '0' else station['V'])
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