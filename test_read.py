from pymodbus.client import ModbusTcpClient
import time

c = ModbusTcpClient('127.0.0.1', port=5022)
print("Connecting...")
c.connect()
time.sleep(0.5)

print("\nTest 1: Read 2 registers from address 0")
r = c.read_holding_registers(0, count=2, device_id=0)
print(f'Result: {r}')
print(f'Is Error: {r.isError()}')
print(f'Registers: {r.registers if hasattr(r, "registers") else "N/A"}')

print("\nTest 2: Read 4 registers from address 1000")
r2 = c.read_holding_registers(1000, count=4, device_id=0)
print(f'Result: {r2}')
print(f'Is Error: {r2.isError()}')
if hasattr(r2, 'registers'):
    print(f'Registers: {r2.registers}')
else:
    print(f'Exception: {r2}')

c.close()
