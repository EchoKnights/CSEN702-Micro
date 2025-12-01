import context

CDB = {} 
CDB_Queue = []

def Enter_CDB_Queue(tag, value):
    global CDB
    global CDB_Queue

    CDB_Queue.append((tag, value))
    print(f"Entered CDB Queue: Tag={tag}, Value={value}")


def write_to_CDB():
    global CDB
    CDB = {}
    if not CDB_Queue:
        return
    payload = CDB_Queue.pop(0)
    CDB['tag'] = payload[0]
    CDB['value'] = payload[1]
    print(f"Written to CDB: {CDB}")
        
def listen_to_CDB():
    global CDB
    if not CDB:
        return
    
    tag = CDB['tag']
    value = CDB['value']
    
    print(f"Listening to CDB: Tag={tag}, Value={value}")

    if tag is None or value is None:
        return
    
    for station in context.adder_reservation_stations.values():
        if station["Qj"] == tag:
            station["Vj"] = value
            station["Qj"] = "0"
        if station["Qk"] == tag:
            station["Vk"] = value
            station["Qk"] = "0"
    
    for station in context.mult_reservation_stations.values():
        if station["Qj"] == tag:
            station["Vj"] = value
            station["Qj"] = "0"
        if station["Qk"] == tag:
            station["Vk"] = value
            station["Qk"] = "0"
    
    for station in context.fp_adder_reservation_stations.values():
        if station["Qj"] == tag:
            station["Vj"] = value
            station["Qj"] = "0"
        if station["Qk"] == tag:
            station["Vk"] = value
            station["Qk"] = "0"
    
    for station in context.fp_mult_reservation_stations.values():
        if station["Qj"] == tag:
            station["Vj"] = value
            station["Qj"] = "0"
        if station["Qk"] == tag:
            station["Vk"] = value
            station["Qk"] = "0"
    
    for reg in context.floating_point_registers.values():
        if reg["Qi"] == tag:
            reg["Value"] = value
            reg["Qi"] = "0"
            
    for buffer in context.store_buffers.values():
        if buffer["Qj"] == tag:
            buffer["Vj"] = value
            buffer["Qj"] = "0"
        if buffer["Qk"] == tag:
            buffer["Vk"] = value
            buffer["Qk"] = "0"

        