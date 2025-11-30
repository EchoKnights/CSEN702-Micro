import context
import fetch
import execute
import wb
import CDB

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
        continue_fetch = fetch.write_to_reservation_station(decoded_instruction)
        if continue_fetch is None:
            print("Stalling.")
            return
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
            print(f'Added {name} to To Be Executed Queue')
            
    for name, station in context.mult_reservation_stations.items():
        if station["busy"] == 1 and (name, station) not in TBE_Queue \
        and (name, station) not in Execute_Queue \
        and (name, station) not in Ready_Queue \
        and (name, station) not in Waiting_Queue \
        and (name, station) not in Result_Queue \
        and (name, station) not in Clear_Queue:
            TBE_Queue.append((name, station))
            print(f'Added {name} to To Be Executed Queue')   
    
    for name, station in context.fp_adder_reservation_stations.items():
        if station["busy"] == 1 and (name, station) not in TBE_Queue \
        and (name, station) not in Execute_Queue \
        and (name, station) not in Ready_Queue \
        and (name, station) not in Waiting_Queue \
        and (name, station) not in Result_Queue \
        and (name, station) not in Clear_Queue:
            TBE_Queue.append((name, station))
            print(f'Added {name} to To Be Executed Queue')
    
    for name, station in context.fp_mult_reservation_stations.items():
        if station["busy"] == 1 and (name, station) not in TBE_Queue \
        and (name, station) not in Execute_Queue \
        and (name, station) not in Ready_Queue \
        and (name, station) not in Waiting_Queue \
        and (name, station) not in Result_Queue \
        and (name, station) not in Clear_Queue:
            TBE_Queue.append((name, station))
            print(f'Added {name} to To Be Executed Queue')
            
    for name, station in context.load_buffers.items():
        if station["busy"] == 1 and (name, station) not in TBE_Queue \
        and (name, station) not in Execute_Queue \
        and (name, station) not in Ready_Queue \
        and (name, station) not in Waiting_Queue \
        and (name, station) not in Result_Queue \
        and (name, station) not in Clear_Queue:
            TBE_Queue.append((name, station))
            print(f'Added {name} to To Be Executed Queue')
            
    for name, station in context.store_buffers.items():
        if station["busy"] == 1 and (name, station) not in TBE_Queue \
        and (name, station) not in Execute_Queue \
        and (name, station) not in Ready_Queue \
        and (name, station) not in Waiting_Queue \
        and (name, station) not in Result_Queue \
        and (name, station) not in Clear_Queue:
            TBE_Queue.append((name, station))
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
    
    for name, station in list(TBE_Queue):
        if name.startswith('FA') or name.startswith('FM'):
            if station['Qj'] in (0, '0') and station['Qk'] in (0, '0'):
                Ready_Queue.append((name, station))
                TBE_Queue.remove((name, station))
            else:
                Waiting_Queue.append((name, station))
                TBE_Queue.remove((name, station))
        elif name.startswith('L'):
            Execute_Queue.append((name, station))
            TBE_Queue.remove((name, station))
        elif name.startswith('S'):
            if station['Q'] == '0':
                Execute_Queue.append((name, station))
                TBE_Queue.remove((name, station))
            else:
                Waiting_Queue.append((name, station))
                TBE_Queue.remove((name, station))
        
    completed = []    
    for name, station in list(Execute_Queue):
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
        elif name.startswith('A'):
            context.adder_reservation_stations[name]['time'] = station['time']
        elif name.startswith('M'):
            context.mult_reservation_stations[name]['time'] = station['time']
        
        if station['time'] == 0:
            print(f"Station {name} has completed execution.")
            completed.append((name, station))
            
    for name, station in completed:
        Result_Queue.append((name, station))
        Execute_Queue.remove((name, station))
        print(f"Station {name} moved from Execute to Result Queue")

    for name, station in list(Waiting_Queue):
        if station['Qj'] in (0, '0') and station['Qk'] in (0, '0'):
            Ready_Queue.append((name, station))
            Waiting_Queue.remove((name, station))
            print(
                f"Station {name} is now ready to execute with values "
                f"Vj={station['Vj']}, Vk={station['Vk']}, "
                f"Qj={station['Qj']}, Qk={station['Qk']}."
            )        
    print('End of Execute Cycle')
    
    for name, station in list(Waiting_Queue):
        if station['Qj'] in (0, '0') and station['Qk'] in (0, '0'):
            print(f'Station {name} is now ready to execute with values Vj={station["Vj"]}, Vk={station["Vk"]}, Qj={station["Qj"]}, Qk={station["Qk"]}.')
            Execute_Queue.append((name, station))
            print(f'Station {name} moved from Waiting to Execute Queue')
            Waiting_Queue.remove((name, station))
        
    
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
        
        print(f'Clearing Clear Queue: {Clear_Queue}')
        Clear_Queue.clear()
    
    if Result_Queue:
        name, station = Result_Queue[0]

        tag = name
        result = execute.execute_instruction(name, station)
        print(f'Station {name} produced result: {result}')
        CDB.Enter_CDB_Queue(tag, result)
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
            for reg_name, reg in context.floating_point_registers.items():
                if reg["Qi"] == name:
                    reg["Value"] = CDB.CDB['value']
                    reg["Qi"] = "0"
            print(f"Reservation station {name} has written back and is now free.")
            Clear_Queue.append((name, station))
            Result_Queue.remove((name, station))
        elif name.startswith('FM'):
            for reg_name, reg in context.floating_point_registers.items():
                if reg["Qi"] == name:
                    reg["Value"] = CDB.CDB['value']
                    reg["Qi"] = "0"
            print(f"Reservation station {name} has written back and is now free.")
            Clear_Queue.append((name, station))
            print(f"Reservation station {name} has written to Clear Queue.")
            Result_Queue.remove((name, station))
        elif name.startswith('L'):
            for reg_name, reg in context.floating_point_registers.items():
                if reg["Qi"] == name:
                    reg["Value"] = CDB.CDB['value']
                    reg["Qi"] = "0"
            print(f"Load buffer {name} has written back and is now free.")
            Clear_Queue.append((name, station))
            Result_Queue.remove((name, station))
        elif name.startswith('A') or name.startswith('M'):
            for reg_name, reg in context.general_registers.items():
                if reg == name:
                    context.general_registers[reg] = CDB.CDB['value']
            print(f"Reservation station {name} has written back and is now free.")
            Clear_Queue.append((name, station))
            Result_Queue.remove((name, station))