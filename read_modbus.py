"""
Modbus TCP Client - Read 3-Phase Electrical Values
Connects to the server and displays the simulated values
Compatible with pymodbus v3.x
"""

import struct
import time
from pymodbus.client import ModbusTcpClient


def registers_to_float(reg_high, reg_low):
    """Convert two 16-bit Modbus registers to a Python float (IEEE 754)"""
    combined = struct.pack('>HH', reg_high, reg_low)
    return struct.unpack('>f', combined)[0]


def read_electrical_values(client):
    """Read all 10 electrical values from the server"""
    try:
        # Read 20 registers (10 float values × 2 registers each) starting at address 1000
        # Use device_id=1 to match standard Modbus unit ID in server
        result = client.read_holding_registers(1000, count=20, device_id=1)
        
        if result.isError():
            print(f"Error reading registers: {result}")
            return None
        
        print(f"raw registers: {result.registers}")
        values = []
        for i in range(0, 20, 2):
            float_value = registers_to_float(result.registers[i], result.registers[i + 1])
            values.append(float_value)
        
        return {
            'voltage_l1': values[0],
            'voltage_l2': values[1],
            'voltage_l3': values[2],
            'voltage_n': values[3],
            'current_l1': values[4],
            'current_l2': values[5],
            'current_l3': values[6],
            'current_n': values[7],
            'total_power': values[8],
            'total_energy': values[9]
        }
    except Exception as e:
        print(f"Error: {e}")
        return None


def display_values(values):
    """Display the electrical values in a formatted way"""
    if values is None:
        return
    
    print("\n" + "="*60)
    print("3-PHASE ELECTRICAL CIRCUIT VALUES")
    print("="*60)
    print(f"{'VOLTAGES':^60}")
    print("-"*60)
    print(f"Voltage L1 (Phase 1):    {values['voltage_l1']:8.2f} V")
    print(f"Voltage L2 (Phase 2):    {values['voltage_l2']:8.2f} V")
    print(f"Voltage L3 (Phase 3):    {values['voltage_l3']:8.2f} V")
    print(f"Voltage N  (Neutral):    {values['voltage_n']:8.2f} V")
    print("-"*60)
    print(f"{'CURRENTS':^60}")
    print("-"*60)
    print(f"Current L1 (Phase 1):    {values['current_l1']:8.2f} A")
    print(f"Current L2 (Phase 2):    {values['current_l2']:8.2f} A")
    print(f"Current L3 (Phase 3):    {values['current_l3']:8.2f} A")
    print(f"Current N  (Neutral):    {values['current_n']:8.2f} A")
    print("-"*60)
    print(f"{'POWER & ENERGY':^60}")
    print("-"*60)
    print(f"Total Power:             {values['total_power']:8.2f} kW")
    print(f"Total Energy:            {values['total_energy']:8.4f} kWh")
    print("="*60)


def main():
    """Main client loop"""
    # Connect to Modbus server on localhost:5023 (no admin privileges needed)
    client = ModbusTcpClient('127.0.0.1', port=5023)
    
    print("Connecting to Modbus TCP Server at localhost:5023...")
    
    if not client.connect():
        print("Failed to connect to server.")
        print("Make sure the server is running: python simple_modbus_server.py")
        return
    
    print("Connected successfully!\n")
    
    max_errors = 10
    error_count = 0
    
    try:
        while True:
            values = read_electrical_values(client)
            
            if values is None:
                error_count += 1
                print(f"[Error {error_count}/{max_errors}]")
                if error_count >= max_errors:
                    print(f"\nExiting after {max_errors} consecutive errors.")
                    break
            else:
                error_count = 0  # Reset error counter on successful read
                display_values(values)
            
            time.sleep(2)  # Update every 2 seconds
    except KeyboardInterrupt:
        print("\n\nClient stopped.")
    finally:
        client.close()


if __name__ == '__main__':
    main()
