import context
import fetch
import execute

def writeback(tag, value):
    for station in context.mult_reservation_stations.values():
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
    
    for buffer in context.store_buffers.values():
        if buffer["Q"] == tag:
            buffer["V"] = value
            buffer["Q"] = "0"
    
    for reg, reg_info in context.floating_point_registers.items():
        if reg_info["Qi"] == tag:
            reg_info["Value"] = value
            reg_info["Qi"] = "0"
        
    for reg in context.general_registers.items():
        if reg == tag:
            context.general_registers[reg] = value
