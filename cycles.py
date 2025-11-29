import context
import fetch
import execute
import wb
import CDB

Execute_Queue = []
Ready_Queue = []
Waiting_Queue = []
Result_Queue = []

def print_state():
    print('\n')
    print(f"State of Load buffers: {context.load_buffers}")
    print('\n')
    print(f"State of Store buffers: {context.store_buffers}")
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
        context.increment_pc(1)
        return instruction
    else:
        print("No more instructions to fetch.")
        return None
    
def fetch_cycle():
    print('Start of Fetch Cycle')
    print('\n')

    instruction = fetch_cycle_helper()
    if instruction is not None:
        decoded_instruction = fetch.decode_instruction(instruction)
        print(f"Decoded instruction: {decoded_instruction}")
        fetch.write_to_reservation_station(decoded_instruction)
        print('End of Fetch Cycle')
    
    for name, station in context.fp_adder_reservation_stations.items():
        if station["busy"] == 1 and (name, station) not in Execute_Queue \
        and (name, station) not in Ready_Queue \
        and (name, station) not in Waiting_Queue \
        and (name, station) not in Result_Queue:
            Execute_Queue.append((name, station))
    
    for name, station in context.fp_mult_reservation_stations.items():
        if station["busy"] == 1 and (name, station) not in Execute_Queue \
        and (name, station) not in Ready_Queue \
        and (name, station) not in Waiting_Queue \
        and (name, station) not in Result_Queue:
            Execute_Queue.append((name, station))
            
    for name, station in context.load_buffers.items():
        if station["busy"] == 1 and (name, station) not in Execute_Queue \
        and (name, station) not in Ready_Queue \
        and (name, station) not in Waiting_Queue \
        and (name, station) not in Result_Queue:
            Execute_Queue.append((name, station))
            
    for name, station in context.store_buffers.items():
        if station["busy"] == 1 and (name, station) not in Execute_Queue \
        and (name, station) not in Ready_Queue \
        and (name, station) not in Waiting_Queue \
        and (name, station) not in Result_Queue:
            Execute_Queue.append((name, station))
    
    print('Current Execute Queue:')
    print(Execute_Queue)
    print('\n')
    print('Current Ready Queue:')
    print(Ready_Queue)
    print('\n')
    print('Current Waiting Queue:')
    print(Waiting_Queue)
    print('\n')
    
def execute_cycle():
    CDB.listen_to_CDB()
    
    for name, station in list(Execute_Queue):
        if name.startswith('FA') or name.startswith('FM'):
            if station['Qj'] in (0, '0') and station['Qk'] in (0, '0'):
                Ready_Queue.append((name, station))
                Execute_Queue.remove((name, station))
            else:
                Execute_Queue.remove((name, station))
                Waiting_Queue.append((name, station))
        elif name.startswith('L'):
            Ready_Queue.append((name, station))
            Execute_Queue.remove((name, station))
        elif name.startswith('S'):
            if station['Q'] == '0':
                Ready_Queue.append((name, station))
                Execute_Queue.remove((name, station))
            else:
                Execute_Queue.remove((name, station))
                Waiting_Queue.append((name, station))
    
    for name, station in list(Waiting_Queue):
        if station['Qj'] in (0, '0') and station['Qk'] in (0, '0'):
            print(f'Station {name} is now ready to execute with values Vj={station["Vj"]}, Vk={station["Vk"]}, Qj={station["Qj"]}, Qk={station["Qk"]}.')
            Ready_Queue.append((name, station))
            print(f'Station {name} moved from Waiting to Ready Queue')
            Waiting_Queue.remove((name, station))
    
    for name, station in list(Ready_Queue):
        station['time'] -= 1
        print(f"Decremented time for station {name}, remaining time: {station['time']}")
        if name.startswith('FA'):
            context.fp_adder_reservation_stations[name]['time'] = station['time']
        elif name.startswith('FM'):
            context.fp_mult_reservation_stations[name]['time'] = station['time']
        elif name.startswith('L'):
            context.load_buffers[name]['time'] = station['time']
        elif name.startswith('S'):
            context.store_buffers[name]['time'] = station['time']
        
        if station['time'] == 0:
            print(f'Station {name} has completed execution.')
            tag = name
            result = execute.execute_instruction(name, station)
            CDB.Enter_CDB_Queue(tag, result)
            Result_Queue.append((name, station))
            Ready_Queue.remove((name, station))
        
    print('End of Execute Cycle')
    
def writeback_cycle():
    CDB.write_to_CDB()

    CDB.listen_to_CDB()
    
    for name, station in context.store_buffers.items():
        if station['busy'] == 1 and station["Q"] in (0, '0'):
            #later: actually write to data_memory using station["address"]
            station["busy"] = 0
            context.store_buffers[name]["busy"] = 0
            print(f"Store buffer {name} has written and is now free.")
            
    for name, station in list(Result_Queue):
        if name.startswith('FA'):
            station["busy"] = 0
            context.fp_adder_reservation_stations[name]["busy"] = 0
            for reg_name, reg in context.floating_point_registers.items():
                if reg["Qi"] == name:
                    reg["Value"] = CDB.CDB['value']
                    reg["Qi"] = "0"
            print(f"Reservation station {name} has written back and is now free.")
            Result_Queue.remove((name, station))
        elif name.startswith('FM'):
            station["busy"] = 0
            context.fp_mult_reservation_stations[name]["busy"] = 0
            for reg_name, reg in context.floating_point_registers.items():
                if reg["Qi"] == name:
                    reg["Value"] = CDB.CDB['value']
                    reg["Qi"] = "0"
            print(f"Reservation station {name} has written back and is now free.")
            Result_Queue.remove((name, station))
        elif name.startswith('L'):
            station["busy"] = 0
            context.load_buffers[name]["busy"] = 0
            for reg_name, reg in context.floating_point_registers.items():
                if reg["Qi"] == name:
                    reg["Value"] = CDB.CDB['value']
                    reg["Qi"] = "0"
            print(f"Load buffer {name} has written back and is now free.")
            Result_Queue.remove((name, station))