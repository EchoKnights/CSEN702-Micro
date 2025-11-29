import context

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
                address = rs + offset
            else:
                immediate = offset_part.strip()
                address = immediate
                
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
        elif (opcode == 26):  #BEQZ
            if len(operands) >= 1:
                rs = operands[0].strip(',')
            if len(operands) >= 2:
                name = operands[1].strip(',')
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
    payload = [opcode, rs, rt, rd, immediate, address]
    opcode = operands = rs = rt = rd = immediate = address = name = val_rs = val_rt = 0
    
    return payload

def write_to_reservation_station(payload):
    opcode = payload[0]
    rs = payload[1]
    rt = payload[2]
    rd = payload[3]
    immediate = payload[4]
    address = payload[5]
    
    print(f"Writing to reservation station with payload: {payload}")
    print({"opcode": opcode, "rs": rs, "rt": rt, "rd": rd, "immediate": immediate, "address": address})
    
    if opcode in range(0, 9):
        print("Writing to Load/Store Buffer")
        write_to_ls_st_buffer(opcode, rd, rs, immediate, address)
    elif opcode in range(9, 15):
        print("Writing to Integer Arithmetic Reservation Station")
    elif opcode in range(15, 23):
        print("Writing to Floating-Point Arithmetic Reservation Station")
        write_to_fp_reservation_station(opcode, rd, rs, rt)
    elif opcode in range(23, 28):
        print("Writing to Control Reservation Station")
    else:
        print("Unknown opcode; cannot write to reservation station")
        
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
    elif flag == "S":
        context.store_buffers[buffer_name]["time"] = context.store_latency
        context.store_buffers[buffer_name]["busy"] = 1
        context.store_buffers[buffer_name]["address"] = address
        val_rt = pull_value_from_register(rs)
        qi_rt = pull_qi_from_register(rs)
        if qi_rt == '0':
            context.store_buffers[buffer_name]["V"] = val_rt
            context.store_buffers[buffer_name]["Q"] = 0
        else:
            context.store_buffers[buffer_name]["V"] = '-'
            context.store_buffers[buffer_name]["Q"] = qi_rt
        print(f"Issued Store instruction to buffer {buffer_name}: {rd}, {rs}, {immediate}")
        

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

    if (pull_qi_from_register(rs) == '0'):
        vj = pull_value_from_register(rs)
        qj = 0
    else:
        vj = '-'
        qj = pull_qi_from_register(rs)

    if (pull_qi_from_register(rt) == '0'):
        vk = pull_value_from_register(rt)
        qk = 0
    else:
        vk = '-'
        qk = pull_qi_from_register(rt)
    if (rd is not None):
        set_in_register(rd, 1, station_name)
    

    if (opcode in (15, 16, 17, 18)):  # ADD.D, ADD.S, SUB.D, SUB.S
        stations[station_name]["time"] = context.fp_add_latency
    elif (opcode in (19, 20, 21, 22)):  # MUL.D, MUL.S, DIV.D, DIV.S
        stations[station_name]["time"] = context.fp_mult_latency
    
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