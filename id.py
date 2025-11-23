import sim_init


def retrieve_value_from_register(register):
    print(f"Retrieving value from register: {register}")
    return sim_init.general_registers.get(register)

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
    opcode = sim_init.isa.get(parts[0], -1)
    operands = parts[1:] if len(parts) > 1 else []

    if (opcode == -1):
        print(f"Warning: Unknown instruction '{instruction}'")
        
    elif (opcode < 9):
        print(f"Decoding Load/Store instruction: {instruction}")
        if len(operands) >= 1:
            rt = operands[0].strip(',')
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
                
        val_rs = retrieve_value_from_register(rs)
        val_rt = retrieve_value_from_register(rt)
        
    elif (9 <= opcode <= 14):
        print(f"Decoding Integer Arithmetic instruction: {instruction}")

        if opcode in (10, 12):
            if len(operands) >= 1:
                rd = operands[0].strip(',')
            if len(operands) >= 2:
                rs = operands[1].strip(',')
            if len(operands) >= 3:
                immediate = operands[2].strip(',').strip('#')
            
            val_rs = retrieve_value_from_register(rs)
            
        else:
            if len(operands) >= 1:
                rd = operands[0].strip(',')
            if len(operands) >= 2:
                rs = operands[1].strip(',')
            if len(operands) >= 3:
                rt = operands[2].strip(',')
                
            val_rs = retrieve_value_from_register(rs)
            val_rt = retrieve_value_from_register(rt)
        
            
    elif (15 <= opcode <= 22):
        print(f"Decoding Floating-Point Arithmetic instruction: {instruction}")
        
        if len(operands) >= 1:
            rd = operands[0].strip(',')
        if len(operands) >= 2:
            rs = operands[1].strip(',')
        if len(operands) >= 3:
            rt = operands[2].strip(',')
            
        val_rs = retrieve_value_from_register(rs)
        val_rt = retrieve_value_from_register(rt)
            
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
                
        val_rs = retrieve_value_from_register(rs)
        val_rt = retrieve_value_from_register(rt)       
    
    payload = [opcode, operands, rs, rt, rd, immediate, address, name, val_rs, val_rt]
    opcode = operands = rs = rt = rd = immediate = address = name = val_rs = val_rt = 0
    
    return payload


def update_id_ex_register(decoded_info):
    global id_ex_register
    id_ex_register = [{"Opcode": opcode, 
                       "Destination Register": rd, 
                       "RS Value": val_rs, 
                       "RT Value": val_rt, 
                       "Immediate": immediate, 
                       "Address": address, 
                       "Name": name, 
                       "Valid Bit": valid_bit} 
                      for opcode, rd, val_rs, val_rt, immediate, address, name, valid_bit in [decoded_info]]