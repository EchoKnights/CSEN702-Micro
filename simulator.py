import context

A1 = context.AdditionBuffer()
A2 = context.AdditionBuffer()
A3 = context.AdditionBuffer()
FA1 = context.FPAdditionBuffer()
FA2 = context.FPAdditionBuffer()
FA3 = context.FPAdditionBuffer()
FM1 = context.FPMultiplicationBuffer()
FM2 = context.FPMultiplicationBuffer()
M1 = context.MultiplicationBuffer()
M2 = context.MultiplicationBuffer()
L1 = context.LoadBuffer()
L2 = context.LoadBuffer()
S1 = context.StoreBuffer()
S2 = context.StoreBuffer()
S3 = context.StoreBuffer()


FPAStation = [FA1, FA2, FA3]
FPMStation = [FM1, FM2]
AStation = [A1, A2, A3]
MStation = [M1, M2]
LStation = [L1, L2]
SStation = [S1, S2, S3]
GeneralRegisters = [context.GeneralRegister() for _ in range(context.GeneralRegister.total_general_registers)]
