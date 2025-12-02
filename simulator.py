import context
import fetch
import execute
import cycles
import CDB


fetch.set_in_register('R1', 0, 10)
fetch.set_in_register('R2', 0, 5)
fetch.set_in_register('R3', 0, 12)
fetch.set_in_register('R10', 0, 77)
fetch.set_in_register('R26', 0, 30)
fetch.set_in_register('R27', 0, 20)

fetch.set_in_register('F1', 0, 5.5)
fetch.set_in_register('F2', 0, 2.0)
fetch.set_in_register('F3', 1, "A3")
fetch.set_in_register('F10', 0, 10.0)
fetch.set_in_register('F11', 0, 17.0)

context.initialize_simulator('instructions.txt')

def done():
    no_more_insts = context.pc >= len(context.instruction_memory)

    all_adders_free = all(not st["busy"] for st in context.fp_adder_reservation_stations.values())
    all_mults_free  = all(not st["busy"] for st in context.fp_mult_reservation_stations.values())
    all_fp_adders_free = all(not st["busy"] for st in context.adder_reservation_stations.values())
    all_fp_mults_free  = all(not st["busy"] for st in context.mult_reservation_stations.values())
    all_loads_free  = all(not st["busy"] for st in context.load_buffers.values())
    all_stores_free = all(not st["busy"] for st in context.store_buffers.values())

    queues_empty = not cycles.TBE_Queue and not cycles.Execute_Queue and not cycles.Ready_Queue \
                   and not cycles.Waiting_Queue and not cycles.Result_Queue \
                   and not CDB.CDB_Queue

    return no_more_insts and all_adders_free and all_fp_adders_free and all_mults_free and all_fp_mults_free and all_loads_free and all_stores_free and queues_empty


while True:
    input("Press Enter to proceed to the next cycle...")
    cycles.increment_cycle()

    cycles.writeback_cycle()

    cycles.execute_cycle()

    cycles.fetch_cycle()

    cycles.print_state()

    if done():
        break
