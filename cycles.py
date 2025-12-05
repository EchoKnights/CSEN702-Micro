import context
import fetch
import execute
import wb
import CDB
import cache

try:
    import gui
    HAS_GUI = True
except ImportError:
    HAS_GUI = False

TBE_Queue = []
Execute_Queue = []
Ready_Queue = []
Waiting_Queue = []
Result_Queue = []
Clear_Queue = []

def print_state():
    print('\n')
    print(f"State of Load buffers: {context.load_buffers}")
    print('\n')
    print(f"State of Store buffers: {context.store_buffers}")
    print('\n')
    print(f"State of integer adder reservation stations: {context.adder_reservation_stations}")
    print('\n')
    print(f"State of integer multiplier reservation stations: {context.mult_reservation_stations}")
    print('\n')
    print(f"State of floating adder reservation stations: {context.fp_adder_reservation_stations}")
    print ('\n')
    print(f'State of floating multiplier reservation stations: {context.fp_mult_reservation_stations}')
    print('\n')
    print(f"State of floating registers: {context.floating_point_registers}")
    print('\n')
    print(f"State of registers: {context.general_registers}")
    print('\n')


def increment_cycle():
    context.clock_cycle += 1
    
    print('----------------------------------------')
    print('\n')
    print(f"Cycle: {context.clock_cycle}")
    print('\n')
    print('----------------------------------------')
    print('\n')
    
    
def fetch_cycle_helper():
    instruction = fetch.get_current_instruction()
    if instruction:
        print(f"Fetched instruction: {instruction}")
        return instruction
    elif context.STALL == True:
        print("Pipeline is Stalled. No instruction fetched.")
        return None
    else:
        print("No more instructions to fetch.")
        return None
    
def fetch_cycle():
    print('Start of Fetch Cycle')
    print('\n')
    print(f'PC at start of fetch: {context.pc}')

    instruction = fetch_cycle_helper()
    if instruction is not None:
        decoded_instruction = fetch.decode_instruction(instruction)
        print(f"Decoded instruction: {decoded_instruction}")
        fetch.write_to_reservation_station(decoded_instruction)
        if context.STALL == True:
            print("Pipeline is Stalled.")
        else:
            context.increment_pc(1)
        print(f'PC after fetch: {context.pc}')
        print('End of Fetch Cycle')
        
    for name, station in context.adder_reservation_stations.items():
        if station["busy"] == 1 and (name, station) not in TBE_Queue \
        and (name, station) not in Execute_Queue \
        and (name, station) not in Ready_Queue \
        and (name, station) not in Waiting_Queue \
        and (name, station) not in Result_Queue \
        and (name, station) not in Clear_Queue:
            TBE_Queue.append((name, station))
            gui.update_instruction_issue(name, context.clock_cycle)
            print(f'Added {name} to To Be Executed Queue')
            
    for name, station in context.mult_reservation_stations.items():
        if station["busy"] == 1 and (name, station) not in TBE_Queue \
        and (name, station) not in Execute_Queue \
        and (name, station) not in Ready_Queue \
        and (name, station) not in Waiting_Queue \
        and (name, station) not in Result_Queue \
        and (name, station) not in Clear_Queue:
            TBE_Queue.append((name, station))
            gui.update_instruction_issue(name, context.clock_cycle)
            print(f'Added {name} to To Be Executed Queue')   
    
    for name, station in context.fp_adder_reservation_stations.items():
        if station["busy"] == 1 and (name, station) not in TBE_Queue \
        and (name, station) not in Execute_Queue \
        and (name, station) not in Ready_Queue \
        and (name, station) not in Waiting_Queue \
        and (name, station) not in Result_Queue \
        and (name, station) not in Clear_Queue:
            TBE_Queue.append((name, station))
            gui.update_instruction_issue(name, context.clock_cycle)
            print(f'Added {name} to To Be Executed Queue')
    
    for name, station in context.fp_mult_reservation_stations.items():
        if station["busy"] == 1 and (name, station) not in TBE_Queue \
        and (name, station) not in Execute_Queue \
        and (name, station) not in Ready_Queue \
        and (name, station) not in Waiting_Queue \
        and (name, station) not in Result_Queue \
        and (name, station) not in Clear_Queue:
            TBE_Queue.append((name, station))
            gui.update_instruction_issue(name, context.clock_cycle)
            print(f'Added {name} to To Be Executed Queue')
            
    for name, station in context.load_buffers.items():
        if station["busy"] == 1 and (name, station) not in TBE_Queue \
        and (name, station) not in Execute_Queue \
        and (name, station) not in Ready_Queue \
        and (name, station) not in Waiting_Queue \
        and (name, station) not in Result_Queue \
        and (name, station) not in Clear_Queue:
            TBE_Queue.append((name, station))
            gui.update_instruction_issue(name, context.clock_cycle)
            print(f'Added {name} to To Be Executed Queue')
            
    for name, station in context.store_buffers.items():
        if station["busy"] == 1 and (name, station) not in TBE_Queue \
        and (name, station) not in Execute_Queue \
        and (name, station) not in Ready_Queue \
        and (name, station) not in Waiting_Queue \
        and (name, station) not in Result_Queue \
        and (name, station) not in Clear_Queue:
            TBE_Queue.append((name, station))
            gui.update_instruction_issue(name, context.clock_cycle)
            print(f'Added {name} to To Be Executed Queue')
            
    
    print('Current To Be Executed Queue:')
    print(TBE_Queue)
    print('\n')
    print('Current Execute Queue:')
    print(Execute_Queue)
    print('\n')
    print('Current Ready Queue:')
    print(Ready_Queue)
    print('\n')
    print('Current Waiting Queue:')
    print(Waiting_Queue)
    print('\n')
    print('Current Result Queue:')
    print(Result_Queue)
    print('\n')
    print('Current Clear Queue:')
    print(Clear_Queue)
    print('\n')
    
def execute_cycle():
    for name, station in list(Ready_Queue):
        Execute_Queue.append((name, station))
        Ready_Queue.remove((name, station))
        print(f'Station {name} moved from Ready to Execute Queue')
        if HAS_GUI and 'inst_index' in station:
            gui.update_instruction_exec_start(station['inst_index'], context.clock_cycle)
    
    for name, station in list(TBE_Queue):
        if name.startswith('FA') or name.startswith('FM'):
            if station['Qj'] in (0, '0') and station['Qk'] in (0, '0'):
                Execute_Queue.append((name, station))
                TBE_Queue.remove((name, station))
                if HAS_GUI and 'inst_index' in station:
                    gui.update_instruction_exec_start(station['inst_index'], context.clock_cycle)
            else:
                Waiting_Queue.append((name, station))
                TBE_Queue.remove((name, station))
        elif name.startswith('L'):
            if station['Qj'] in (0, '0') and station.get('A') not in (None, '', '-'):
                try:
                    address = int(station['Vj']) + int(station['A'])
                    cache_status = cache.check_cache_status(address)
                    if cache_status == 'hit':
                        station['time'] = context.load_latency + context.cache_hit_latency
                    else:
                        station['time'] = context.load_latency + context.cache_miss_penalty
                    context.load_buffers[name]['time'] = station['time']
                except:
                    pass
            
            Execute_Queue.append((name, station))
            TBE_Queue.remove((name, station))
            if HAS_GUI and 'inst_index' in station:
                gui.update_instruction_exec_start(station['inst_index'], context.clock_cycle)
        elif name.startswith('S'):
            if station['Qj'] in (0, '0') and station['Qk'] in (0, '0'):
                if station.get('A') not in (None, '', '-'):
                    try:
                        address = int(station['Vj']) + int(station['A'])
                        cache_status = cache.check_cache_status(address)
                        if cache_status == 'hit':
                            station['time'] = context.store_latency + context.cache_hit_latency
                        else:
                            station['time'] = context.store_latency + context.cache_miss_penalty
                        context.store_buffers[name]['time'] = station['time']
                    except:
                        pass
                
                Execute_Queue.append((name, station))
                TBE_Queue.remove((name, station))
                if HAS_GUI and 'inst_index' in station:
                    gui.update_instruction_exec_start(station['inst_index'], context.clock_cycle)
            else:
                Waiting_Queue.append((name, station))
                TBE_Queue.remove((name, station))
        
        if name.startswith('A') or name.startswith('M'):
            if station['Qj'] in (0, '0') and station['Qk'] in (0, '0'):
                Execute_Queue.append((name, station))
                TBE_Queue.remove((name, station))
                if HAS_GUI and 'inst_index' in station:
                    gui.update_instruction_exec_start(station['inst_index'], context.clock_cycle)
            else:
                Waiting_Queue.append((name, station))
                TBE_Queue.remove((name, station))
        
    completed = []    
    for name, station in list(Execute_Queue):
        station['time'] -= 1
        print(f"Decremented time for station {name}, remaining time: {station['time']}")
        if HAS_GUI and 'inst_index' in station:
            if 'exec_cycles' not in station:
                station['exec_cycles'] = 0
            station['exec_cycles'] += 1
            gui.update_instruction_stat(station['inst_index'], "exec_cycles", station['exec_cycles'])
        if name.startswith('FA'):
            context.fp_adder_reservation_stations[name]['time'] = station['time']
        elif name.startswith('FM'):
            context.fp_mult_reservation_stations[name]['time'] = station['time']
        elif name.startswith('L'):
            context.load_buffers[name]['time'] = station['time']
        elif name.startswith('S'):
            context.store_buffers[name]['time'] = station['time']
        elif name.startswith('A'):
            context.adder_reservation_stations[name]['time'] = station['time']
        elif name.startswith('M'):
            context.mult_reservation_stations[name]['time'] = station['time']
        
        if station['time'] == 0:
            print(f"Station {name} has completed execution.")
            result = execute.execute_instruction(name, station)
            station['result'] = result
            completed.append((name, station))
            
    for name, station in completed:
        Result_Queue.append((name, station))
        Execute_Queue.remove((name, station))
        print(f"Station {name} moved from Execute to Result Queue with result: {station.get('result', 'None')}")
        if HAS_GUI and 'inst_index' in station:
            gui.update_instruction_exec_end(station['inst_index'], context.clock_cycle)

    for name, station in list(Waiting_Queue):
        if station['Qj'] in (0, '0') and station['Qk'] in (0, '0'):
            print(
                f"Station {name} is now ready to execute with values "
                f"Vj={station['Vj']}, Vk={station['Vk']}, "
                f"Qj={station['Qj']}, Qk={station['Qk']}."
            )
            Execute_Queue.append((name, station))
            print(f'Station {name} moved from Waiting to Execute Queue')
            if HAS_GUI and 'inst_index' in station:
                gui.update_instruction_exec_start(station['inst_index'], context.clock_cycle)
            Waiting_Queue.remove((name, station))
        
    print('End of Execute Cycle')
        
    
def writeback_cycle():
    if Clear_Queue:
        for name, station in Clear_Queue:
            station["busy"] = 0
            if name.startswith('FA'):
                context.fp_adder_reservation_stations[name]["busy"] = 0
            elif name.startswith('FM'):
                context.fp_mult_reservation_stations[name]["busy"] = 0
            elif name.startswith('L'):
                context.load_buffers[name]["busy"] = 0
            elif name.startswith('S'):
                context.store_buffers[name]["busy"] = 0
            elif name.startswith('A'):
                context.adder_reservation_stations[name]["busy"] = 0
            elif name.startswith('M'):
                context.mult_reservation_stations[name]["busy"] = 0
        
        print(f'Clearing Clear Queue: {[n for n, s in Clear_Queue]}')
        Clear_Queue.clear()
    
    for name, station in list(Result_Queue):
        result = station.get('result')
        
        if name.startswith('S'):
            print(f"Store buffer {name} has completed and is now free.")
            if HAS_GUI and 'inst_index' in station:
                gui.update_instruction_writeback(station['inst_index'], context.clock_cycle)
            Clear_Queue.append((name, station))
            Result_Queue.remove((name, station))
            continue
        
        if station.get('op') in (26, 27):
            print(f"Control instruction at {name} has completed.")
            if HAS_GUI and 'inst_index' in station:
                gui.update_instruction_writeback(station['inst_index'], context.clock_cycle)
            Clear_Queue.append((name, station))
            Result_Queue.remove((name, station))
            continue
        
        if result is not None:
            tag = name
            print(f'Station {name} writing result {result} to CDB')
            CDB.Enter_CDB_Queue(tag, result)
            CDB.write_to_CDB()
            CDB.listen_to_CDB()
            
            cdb_value = CDB.CDB.get('value')
            if cdb_value is not None:
                if name.startswith('FA') or name.startswith('FM') or name.startswith('L'):
                    for reg_name, reg in context.floating_point_registers.items():
                        if reg["Qi"] == name:
                            reg["Value"] = cdb_value
                            reg["Qi"] = "0"
                            print(f"Updated register {reg_name} with value {cdb_value}")
                elif name.startswith('A') or name.startswith('M'):
                    for reg_name, reg in context.general_registers.items():
                        if reg["Qi"] == name:
                            reg["Value"] = cdb_value
                            reg["Qi"] = "0"
                            print(f"Updated register {reg_name} with value {cdb_value}")
                    for reg_name, reg in context.floating_point_registers.items():
                        if reg["Qi"] == name:
                            reg["Value"] = cdb_value
                            reg["Qi"] = "0"
                            print(f"Updated register {reg_name} with value {cdb_value}")
            
            print(f"Reservation station {name} has written back and is now free.")
            if HAS_GUI and 'inst_index' in station:
                gui.update_instruction_writeback(station['inst_index'], context.clock_cycle)
            Clear_Queue.append((name, station))
            Result_Queue.remove((name, station))
    
    print_state()