import context
import simulator as sim_init

def pull_next_instruction():
    if context.pc < len(context.instruction_memory):
        instruction = context.instruction_memory[context.pc]
        context.increment_pc(1)
        return instruction
    else:
        return None
    
def retrieve_value_from_register(register):
    """Return the integer/float value stored in a general register.

    Accepted formats: 'R0', 'r1', or numeric strings '0'. Returns 0 for
    None/unparseable registers or when the register index is out of range.
    """
    if not register:
        return 0
    reg = str(register).replace(',', '').strip()
    # support formats like R1 or 1
    if reg == '':
        return 0
    if reg.upper().startswith('R'):
        idx_part = reg[1:]
    else:
        idx_part = reg
    try:
        idx = int(idx_part)
    except Exception:
        return 0

    regs = getattr(sim_init, 'GeneralRegisters', None)
    if regs and 0 <= idx < len(regs):
        return regs[idx].value
    return 0

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

def load_instruction_into_station(payload):
    if(payload is None or len(payload) == 0 or payload[0] is None or payload[0] == -1 or payload[0] == 0):
        return None
    opcode = payload[0]

    # Integer arithmetic
    if 9 <= opcode <= 14:
        # MUL/DIV -> integer multiplication station; else addition station
        if opcode in (13, 14):
            stations = getattr(sim_init, 'MStation', [])
        else:
            stations = getattr(sim_init, 'AStation', [])

        for s in stations:
            if not s.busy:
                s.busy = True
                s.Tag = context.tag
                context.tag += 1
                s.opcode = opcode
                # value fields (may be 0)
                try:
                    s.Vj = payload[8]
                    s.Vk = payload[9]
                except Exception:
                    pass
                return s
        return None

    # Floating point arithmetic
    if 15 <= opcode <= 22:
        # choose FP multiply station for FP mul/div, else FP add
        if opcode in (19, 20, 21, 22):
            stations = getattr(sim_init, 'FPMStation', [])
        else:
            stations = getattr(sim_init, 'FPAStation', [])

        for s in stations:
            if not s.busy:
                s.busy = True
                s.Tag = context.tag
                context.tag += 1
                s.opcode = opcode
                try:
                    s.Vj = float(payload[8])
                    s.Vk = float(payload[9])
                except Exception:
                    # keep defaults if conversion fails
                    pass
                return s
        return None

    # Load / Store
    if opcode < 9:
        # Loads
        if opcode in (1, 2, 3, 4):
            stations = getattr(sim_init, 'LStation', [])
            for s in stations:
                if not s.busy:
                    s.busy = True
                    s.Tag = context.tag
                    context.tag += 1
                    s.opcode = opcode
                    # store address (payload[6])
                    try:
                        s.address = payload[6]
                    except Exception:
                        pass
                    return s
            return None

        # Stores
        if opcode in (5, 6, 7, 8):
            stations = getattr(sim_init, 'SStation', [])
            for s in stations:
                if not s.busy:
                    s.busy = True
                    s.Tag = context.tag
                    context.tag += 1
                    s.opcode = opcode
                    try:
                        s.address = payload[6]
                        s.V = payload[9]
                        s.Q = None
                    except Exception:
                        pass
                    return s
            return None

    # Control / other instructions: not handled by reservation stations here
    return None