import context

labels = {}

def get_current_instruction():
    pc = context.pc
    if pc < len(context.instruction_memory) and context.STALL == False:
        instruction = context.instruction_memory[pc]
        return instruction
    return None

def pull_value_from_register(register):
    if not register:
        return 0
    register = register.strip()
    if register.startswith('F'):
        return context.floating_point_registers[register]["Value"]
    return context.general_registers[register]["Value"]
    
def pull_qi_from_register(register):
    if not register:
        return 0
    register = register.strip()
    if register.startswith('F'):
        return context.floating_point_registers[register]["Qi"]
    return context.general_registers[register]["Qi"]
    
def set_in_register(register, tag, value):
    if not register:
        return
    register = register.strip()

    if tag == 0:
        if register.startswith('F'):
            context.floating_point_registers[register]["Value"] = value
        else:
            context.general_registers[register]["Value"] = value
    else:
        if register.startswith('F'):
            context.floating_point_registers[register]["Qi"] = value
        else:
            context.general_registers[register]["Qi"] = value
    
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
        elif ((opcode == 26) or (opcode == 27)):  #BEQ or BNE
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
        print("Handling Control Instruction")
        write_control_instruction(opcode, rs, rt, immediate, name)
        context.stall_pipeline()
        return 0
    else:
        print("Unknown opcode; cannot write to reservation station")
        return None
        
def write_to_ls_st_buffer(opcode, rd, rs, immediate, address):
    buffer_name = None
    flag = ""
    qk = 0
    vk = 0
    
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
        context.stall_pipeline()
        return None
    context.unstall_pipeline()
    
    if (pull_qi_from_register(rs) in (0, '0')):
        vj = pull_value_from_register(rs)
        qj = 0
    else:
        vj = '-'
        qj = pull_qi_from_register(rs)

    if (rd is not None) and (flag == "L"):
        set_in_register(rd, 1, buffer_name)     
        
    if (flag == "L"):
        buffers = context.load_buffers
        buffers[buffer_name]["time"] = context.load_latency
        buffers[buffer_name]["op"] = opcode
        buffers[buffer_name]['busy'] = 1
        if qj == 0:
            buffers[buffer_name]["Vj"] = vj
            buffers[buffer_name]["Qj"] = 0
            buffers[buffer_name]["A"] = address
        else:
            buffers[buffer_name]["Vj"] = '-'
            buffers[buffer_name]["Qj"] = qj
            buffers[buffer_name]["A"] = immediate
    elif (flag == "S"):
        if (rd):
            if (pull_qi_from_register(rd) in (0, '0')):
                vk = pull_value_from_register(rd)
                qk = 0
            else:
                vk = '-'
                qk = pull_qi_from_register(rd)
        
        
        buffers = context.store_buffers
        buffers[buffer_name]["time"] = context.store_latency
        buffers[buffer_name]["op"] = opcode
        buffers[buffer_name]['busy'] = 1
        if qj == 0:
            buffers[buffer_name]["Vj"] = vj
            buffers[buffer_name]["Qj"] = 0
            buffers[buffer_name]["A"] = address
        else:
            buffers[buffer_name]["Vj"] = '-'
            buffers[buffer_name]["Qj"] = qj
            buffers[buffer_name]["A"] = immediate
        if qk == 0:
            buffers[buffer_name]["Vk"] = vk
            buffers[buffer_name]["Qk"] = 0
        else:
            buffers[buffer_name]["Vk"] = '-'
            buffers[buffer_name]["Qk"] = qk
            
    print(f"Issued Load/Store instruction to buffer {buffer_name}: {rd}, {rs}, {immediate}, {address}")
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
        context.stall_pipeline()
        return None
    context.unstall_pipeline()

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
    else:
        stations[station_name]["Vj"] = '-'
        stations[station_name]["Qj"] = qj
        

        
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
        context.stall_pipeline()
        return None
    context.unstall_pipeline()

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

def write_control_instruction(op, rs, rt, immediate, name):
    print(f"Writing control instruction: op={op}, rs={rs}, rt={rt}, immediate={immediate}, name={name}")
    prefix = ''
    stations = {}
    if (op in (26, 27)): #BEQ OR BNE
        stations = context.adder_reservation_stations
        prefix = 'A'
    
    station_name = None
    i = 1
    while f"{prefix}{i}" in stations:
        if stations[f"{prefix}{i}"]["busy"] == 0:
            station_name = f"{prefix}{i}"
            break
        i += 1
        
    if station_name is None:
        print("No free adder reservation station available for control instruction")
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
        
    stations[station_name]["busy"] = 1
    stations[station_name]["op"] = op
    stations[station_name]["A"] = name
        
    stations[station_name]["time"] = 1
    
    if (pull_qi_from_register(rs) in (0, '0')):
        stations[station_name]["Vj"] = vj
        stations[station_name]["Qj"] = 0
    else:
        stations[station_name]["Vj"] = '-'
        stations[station_name]["Qj"] = qj
    if (pull_qi_from_register(rt) in (0, '0')):
        stations[station_name]["Vk"] = vk
        stations[station_name]["Qk"] = 0
    else:
        stations[station_name]["Vk"] = '-'
        stations[station_name]["Qk"] = qk
        
    print(f"Issued Control instruction to station {station_name}: op={op}, rs={rs}, rt={rt}, name={name}")
    return 0
