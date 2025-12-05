import context

def convert_to_binary(number):
    if not isinstance(number, int):
        number = int(number)

    width = context.address_size

    min_val = -(1 << (width - 1))
    max_val = (1 << (width - 1)) - 1
    if number < min_val or number > max_val:
        print(f"Warning: value {number} does not fit in {width}-bit signed range [{min_val}, {max_val}]")
        return None

    mask = (1 << width) - 1
    result = format(number & mask, f"0{width}b")
    print(result)
    return result

def convert_to_decimal(binary_str):
    value = int(binary_str, 2)
    width = len(binary_str)
    if binary_str[0] == '1':
        value -= (1 << width)
    return value

def load_from_data_memory(address, flag='S'):
    data_binary = ''
    if flag == 'S':
        for i in range(context.single_word_size):
            if address + i >= len(context.data_memory):
                print(f"Error: Address {address + i} out of bounds")
                return None
            data_binary += context.data_memory[address + i]
    elif flag == 'D':
        for i in range(context.double_word_size):
            if address + i >= len(context.data_memory):
                print(f"Error: Address {address + i} out of bounds")
                return None
            data_binary += context.data_memory[address + i]
    return data_binary

def store_to_data_memory(address, data, flag = 'S'):
    if flag == 'S':
        for i in range(context.single_word_size):
            if address + i >= len(context.data_memory):
                print(f"Error: Address {address + i} out of bounds")
                return
            context.data_memory[address + i] = data[i * 8:(i + 1) * 8]
    elif flag == 'D':
        for i in range(context.double_word_size):
            if address + i >= len(context.data_memory):
                print(f"Error: Address {address + i} out of bounds")
                return
            context.data_memory[address + i] = data[i * 8:(i + 1) * 8]

def load_into_cache(address):
    binary_address = convert_to_binary(address)
    if binary_address is None:
        return

    tag = binary_address[:context.tag]
    index = binary_address[context.tag:context.tag + context.index]
    block_offset = binary_address[context.tag + context.index:]

    set_index = convert_to_decimal(index)

    if set_index < 0 or set_index >= len(context.cache):
        print(f"Error: Invalid cache set index {set_index} for address {address}")
        return

    block_base = address - (address % context.block_size)
    block_data = []
    for i in range(context.block_size):
        addr = block_base + i
        if addr < len(context.data_memory):
            block_data.append(context.data_memory[addr])
        else:
            # Out of bounds - pad with zeros
            block_data.append('00000000')

    context.cache[set_index]["valid"] = 1
    context.cache[set_index]["tag"] = tag
    context.cache[set_index]["data"] = block_data

    print(f"Loaded address {address} (block {block_base}) into cache line {set_index}")

def check_cache_status(address):
    """
    Check if address is in cache (hit) or not (miss).
    Returns: 'hit' or 'miss'
    """
    binary_address = convert_to_binary(address)
    if binary_address is None:
        return 'miss'

    tag = binary_address[:context.tag]
    index = binary_address[context.tag:context.tag + context.index]
    set_index = convert_to_decimal(index)

    if set_index < 0 or set_index >= len(context.cache):
        return 'miss'
        
    if set_index not in context.cache:
        return 'miss'
        
    line = context.cache[set_index]

    if line["valid"] == 1 and line["tag"] == tag:
        return 'hit'
    
    return 'miss'

def search_cache(address, num_bytes=4):
    binary_address = convert_to_binary(address)
    if binary_address is None:
        return None

    tag = binary_address[:context.tag]
    index = binary_address[context.tag:context.tag + context.index]
    block_offset = binary_address[context.tag + context.index:]

    set_index = convert_to_decimal(index)
    offset = convert_to_decimal(block_offset)

    if set_index < 0 or set_index >= len(context.cache) or set_index not in context.cache:
        print(f"Cache miss for address {address} - invalid set index {set_index}")
        return None

    line = context.cache[set_index]

    if line["valid"] == 1 and line["tag"] == tag:
        print(f"Cache hit for address {address}")
        
        if offset + num_bytes > len(line["data"]):
            print(f"Error: Cache data access out of bounds")
            return None

        bytes_needed = line["data"][offset : offset + num_bytes]
        return ''.join(bytes_needed)

    print(f"Cache miss for address {address}")
    return None

def write_into_cache(address, value, num_bytes=4):
    if isinstance(value, (int, float)):
        if num_bytes == 4:
            if value < 0:
                value = (1 << 32) + int(value)
            else:
                value = int(value)
            data_binary = format(value & 0xFFFFFFFF, '032b')
        else:
            if value < 0:
                value = (1 << 64) + int(value)
            else:
                value = int(value)
            data_binary = format(value & 0xFFFFFFFFFFFFFFFF, '064b')
    else:
        data_binary = str(value)
        if len(data_binary) < num_bytes * 8:
            data_binary = data_binary.zfill(num_bytes * 8)
    
    binary_address = convert_to_binary(address)
    if binary_address is None:
        return

    tag = binary_address[:context.tag]
    index = binary_address[context.tag:context.tag + context.index]
    block_offset = binary_address[context.tag + context.index:]

    set_index = convert_to_decimal(index)
    offset = convert_to_decimal(block_offset)

    for i in range(num_bytes):
        if address + i < len(context.data_memory):
            byte_str = data_binary[i * 8:(i + 1) * 8]
            context.data_memory[address + i] = byte_str

    line = context.cache[set_index]

    if line["valid"] == 1 and line["tag"] == tag:
        print(f"Cache hit for address {address} on write")
        for i in range(num_bytes):
            if offset + i < len(line["data"]):
                line["data"][offset + i] = data_binary[i * 8:(i + 1) * 8]
    else:
        print(f"Cache miss for address {address} on write - loading block into cache")
        load_into_cache(address)
        line = context.cache[set_index]
        for i in range(num_bytes):
            if offset + i < len(line["data"]):
                line["data"][offset + i] = data_binary[i * 8:(i + 1) * 8]