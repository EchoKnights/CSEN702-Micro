import context

labels = {}

def get_current_instruction():
    pc = context.pc
    if pc < len(context.instruction_memory):
        instruction = context.instruction_memory[pc]
        return instruction
    return None

def pull_value_from_register(register):
    if not register:
        return 0
    register = register.strip()
    if register.startswith('F'):
        return context.floating_point_registers[register]["Value"]
    return context.general_registers[register][0]
    
def pull_qi_from_register(register):
    if not register:
        return 0
    register = register.strip()
    if register.startswith('F'):
        return context.floating_point_registers[register]["Qi"]
    return 0
    
def set_in_register(register, tag, value):
    if not register:
        return
    register = register.strip()

    if tag == 0:
        if register.startswith('F'):
            context.floating_point_registers[register]["Value"] = value
        else:
            context.general_registers[register][0] = value
    else:
        if register.startswith('F'):
            context.floating_point_registers[register]["Qi"] = value
        else:
            return

    
def decode_instruction(instruction):
    rs = None
    rt = None
    rd = None
    immediate = None
    address = None
    name = ""
    
    val_rs = 0
    val_rt = 0
    
    parts = instruction.split()
    if (parts[0].endswith(':')):
        label = parts[0][:-1]
        labels[label] = context.pc
        parts = parts[1:]
        
    print(f"Labels: {labels}")

    opcode = context.isa.get(parts[0], -1)
    operands = parts[1:] if len(parts) > 1 else []

    if (opcode == -1):
        print(f"Warning: Unknown instruction '{instruction}'")
        
    elif (opcode < 9):
        print(f"Decoding Load/Store instruction: {instruction}")
        if len(operands) >= 1:
            rd = operands[0].strip(',')
        if len(operands) >= 2:
            offset_part = operands[1]
            if '(' in offset_part and ')' in offset_part:
                offset, rs_part = offset_part.split('(')
                rs = rs_part.strip(')')
                immediate = offset.strip()
                rs_val = pull_value_from_register(rs)
                address = str(int(immediate) + int(rs_val))
            else:
                immediate = offset_part.strip()
                
        if (5 <= opcode):
            temp = rs
            rs = rd
            rd = temp 
            
        val_rs = pull_value_from_register(rs)
        val_rt = pull_value_from_register(rt)
        
    elif (9 <= opcode <= 14):
        print(f"Decoding Integer Arithmetic instruction: {instruction}")

        if opcode in (10, 12):
            if len(operands) >= 1:
                rd = operands[0].strip(',')
            if len(operands) >= 2:
                rs = operands[1].strip(',')
            if len(operands) >= 3:
                immediate = operands[2].strip(',').strip('#')
            
            val_rs = pull_value_from_register(rs)
            
        else:
            if len(operands) >= 1:
                rd = operands[0].strip(',')
            if len(operands) >= 2:
                rs = operands[1].strip(',')
            if len(operands) >= 3:
                rt = operands[2].strip(',')
                
            val_rs = pull_value_from_register(rs)
            val_rt = pull_value_from_register(rt)
        
            
    elif (15 <= opcode <= 22):
        print(f"Decoding Floating-Point Arithmetic instruction: {instruction}")
        
        if len(operands) >= 1:
            rd = operands[0].strip(',')
        if len(operands) >= 2:
            rs = operands[1].strip(',')
        if len(operands) >= 3:
            rt = operands[2].strip(',')
            
        val_rs = pull_value_from_register(rs)
        val_rt = pull_value_from_register(rt)
            
    elif (23 <= opcode <= 27):
        print(f"Decoding Control instruction: {instruction}")
        
        if (opcode == 23):  #J
            if len(operands) >= 1:
                name = operands[0].strip(',')
        elif (opcode == 24):  #JR
            if len(operands) >= 1:
                rs = operands[0].strip(',')
        elif (opcode == 25):  #JAL
            if len(operands) >= 1:
                name = operands[0].strip(',')
        elif (opcode == 26):  #BEQ
            if len(operands) >= 1:
                rs = operands[0].strip(',')
                print(f"BEQ rs: {rs}")
            if len(operands) >= 2:
                rt = operands[1].strip(',')
            if len(operands) >= 3:
                name = operands[2].strip(',')
        elif (opcode == 27):  #BNE
            if len(operands) >= 1:
                rs = operands[0].strip(',')
            if len(operands) >= 2:
                rt = operands[1].strip(',')
            if len(operands) >= 3:
                name = operands[2].strip(',')  
                
        val_rs = pull_value_from_register(rs)
        val_rt = pull_value_from_register(rt)       
    
    testpayload = [opcode, operands, rs, rt, rd, immediate, address, name, val_rs, val_rt]
    payload = [opcode, rs, rt, rd, immediate, address, name]
    opcode = operands = rs = rt = rd = immediate = address = name = val_rs = val_rt = 0
    
    return payload

def write_to_reservation_station(payload):
    opcode = payload[0]
    rs = payload[1]
    rt = payload[2]
    rd = payload[3]
    immediate = payload[4]
    address = payload[5]
    name = payload[6]
    
    print(f"Writing to reservation station with payload: {payload}")
    print({"opcode": opcode, "rs": rs, "rt": rt, "rd": rd, "immediate": immediate, "address": address})
    
    if opcode in range(0, 9):
        print("Writing to Load/Store Buffer")
        return write_to_ls_st_buffer(opcode, rd, rs, immediate, address)
    elif opcode in range(9, 15):
        print("Writing to Integer Arithmetic Reservation Station")
        return write_to_integer_reservation_station(opcode, rd, rs, rt, immediate)
    elif opcode in range(15, 23):
        print("Writing to Floating-Point Arithmetic Reservation Station")
        return write_to_fp_reservation_station(opcode, rd, rs, rt)
    elif opcode in range(23, 28):
        return 0
    else:
        print("Unknown opcode; cannot write to reservation station")
        return None
        
def write_to_ls_st_buffer(opcode, rd, rs, immediate, address):
    buffer_name = None
    flag = ""
    
    if (1 <= opcode <= 4):  # L
        i = 1
        flag = "L"
        while f"L{i}" in context.load_buffers:
            if context.load_buffers[f"L{i}"]["busy"] == 0:
                buffer_name = f"L{i}"
                break
            i += 1
    elif (5 <= opcode <= 8):  # S
        i = 1
        flag = "S"
        while f"S{i}" in context.store_buffers:
            if context.store_buffers[f"S{i}"]["busy"] == 0:
                buffer_name = f"S{i}"
                break
            i += 1
            
    if buffer_name is None:
        print("No free Load/Store buffer available")
        return None
    
    if flag == "L":
        context.load_buffers[buffer_name]["time"] = context.load_latency
        context.load_buffers[buffer_name]["busy"] = 1
        context.load_buffers[buffer_name]["address"] = address
        set_in_register(rd, 1, buffer_name)
        print(f"Issued Load instruction to buffer {buffer_name}: {rd}, {rs}, {immediate}")
        return 0
    elif flag == "S":
        context.store_buffers[buffer_name]["time"] = context.store_latency
        context.store_buffers[buffer_name]["busy"] = 1
        context.store_buffers[buffer_name]["address"] = address
        val_rt = pull_value_from_register(rs)
        qi_rt = pull_qi_from_register(rs)
        if qi_rt in (0, '0'):
            context.store_buffers[buffer_name]["V"] = val_rt
            context.store_buffers[buffer_name]["Q"] = 0
        else:
            context.store_buffers[buffer_name]["V"] = '-'
            context.store_buffers[buffer_name]["Q"] = qi_rt
        print(f"Issued Store instruction to buffer {buffer_name}: {rd}, {rs}, {immediate}")
        return 0
        
        
def write_to_integer_reservation_station(opcode, rd, rs, rt, immediate):
    if opcode in (10, 12):  # DADDI, DSUBI
        stations = context.adder_reservation_stations
        prefix = "A"
    else:
        return None
    
    station_name = None
    i = 1
    while f"{prefix}{i}" in stations:
        if stations[f"{prefix}{i}"]["busy"] == 0:
            station_name = f"{prefix}{i}"
            break
        i += 1
    
    if station_name is None:
        print("No free Integer reservation station available")
        return None

    if (pull_qi_from_register(rs) in (0, '0')):
        vj = pull_value_from_register(rs)
        qj = 0
    else:
        vj = '-'
        qj = pull_qi_from_register(rs)
    if (rd is not None):
        set_in_register(rd, 1, station_name)
    
    if (opcode in (10, 12)):  # DADDI, DSUBI
        stations[station_name]["time"] = context.add_latency
        
    stations[station_name]["busy"] = 1
    stations[station_name]["op"] = opcode
    stations[station_name]["A"] = immediate
    
    if qj == 0:
        stations[station_name]["Vj"] = vj
        stations[station_name]["Qj"] = 0
        print(1)
    else:
        stations[station_name]["Vj"] = '-'
        stations[station_name]["Qj"] = qj
        print(2)
        

        
    print(f"Issued Integer instruction to station {station_name}: {rd}, {rs}, {immediate}")
    return 0
   
   
def write_to_fp_reservation_station(opcode, rd, rs, rt):
    
    if opcode in range(15, 19):   # ADD.D, ADD.S, SUB.D, SUB.S
        stations = context.fp_adder_reservation_stations
        prefix = "FA"
    elif opcode in range(19, 23): # MUL.D, MUL.S, DIV.D, DIV.S
        stations = context.fp_mult_reservation_stations
        prefix = "FM"
    else:
        return None
    
    station_name = None
    i = 1
    while f"{prefix}{i}" in stations:
        if stations[f"{prefix}{i}"]["busy"] == 0:
            station_name = f"{prefix}{i}"
            break
        i += 1

    if station_name is None:
        print("No free FP reservation station available")
        return None

    if (pull_qi_from_register(rs) in (0, '0')):
        vj = pull_value_from_register(rs)
        qj = 0
    else:
        vj = '-'
        qj = pull_qi_from_register(rs)

    if (pull_qi_from_register(rt) in (0, '0')):
        vk = pull_value_from_register(rt)
        qk = 0
    else:
        vk = '-'
        qk = pull_qi_from_register(rt)
    if (rd is not None):
        set_in_register(rd, 1, station_name)
    

    if (opcode in (15, 16, 17, 18)):  # ADD.D, ADD.S, SUB.D, SUB.S
        stations[station_name]["time"] = context.fp_add_latency
    elif (opcode in (19, 20)):  # MUL.D, MUL.S, DIV.D, DIV.S
        stations[station_name]["time"] = context.fp_mult_latency
    elif (opcode in (21, 22)):
        stations[station_name]["time"] = context.fp_div_latency
    
    stations[station_name]["busy"] = 1
    stations[station_name]["op"] = opcode
    stations[station_name]["A"] = ""

    if qj == 0:
        stations[station_name]["Vj"] = vj
        stations[station_name]["Qj"] = 0
    else:
        stations[station_name]["Vj"] = '-'
        stations[station_name]["Qj"] = qj

    if qk == 0:
        stations[station_name]["Vk"] = vk
        stations[station_name]["Qk"] = 0
    else:
        stations[station_name]["Vk"] = '-'
        stations[station_name]["Qk"] = qk

    print(f"Issued FP instruction to station {station_name}: {rd}, {rs}, {rt}")
    return 0

def handle_loop_instruction(opcode, rs_value, rt_value, name):
    new_pc = None
    new_pc = compute_loopback_address(name)
    do_loop = compute_if_loop(rs_value, rt_value, opcode)

def compute_if_loop(rs_value, rt_value, opcode):
    if opcode == 26:  # BEQ
        return rs_value == rt_value
    elif opcode == 27:  # BNE
        return rs_value != rt_value
    return False

def compute_loopback_address(label):
    if label in labels:
        return labels[label]
    else:
        print(f"Error: Label '{label}' not found.")
        return 0