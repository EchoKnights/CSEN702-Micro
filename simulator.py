import context
import fetch



fetch.set_in_register('R1', 0, 10)
fetch.set_in_register('R2', 0, 20)
fetch.set_in_register('R10', 0, 77)

fetch.set_in_register('F1', 0, 5.5)
fetch.set_in_register('F2', 0, 2.0)
fetch.set_in_register('F3', 1, "A3")
context.initialize_reservation_stations()

print("Enter example instruction:")
example_instruction = input().strip()

print(f"Decoding instruction: {example_instruction}")
decoded = fetch.decode_instruction(example_instruction)
station = fetch.write_to_reservation_station(decoded)
print('\n')
print(f"State of Load buffers: {context.load_buffers}")
print('\n')
print(f"State of Store buffers: {context.store_buffers}")
print('\n')
print(f"State of reservation stations: {context.fp_adder_reservation_stations}")
print('\n')
print(f"State of floating registers: {context.floating_point_registers}")
print('\n')
print(f"State of registers: {context.general_registers}")
print('\n')
