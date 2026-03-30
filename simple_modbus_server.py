"""
Modbus TCP Server - 3-Phase Electrical Values Simulator
Hosts on localhost:5022 with 10 floating-point values stored as holding registers
Compatible with pymodbus v3.x using async model
"""

import asyncio
import struct
import math
import time
from pymodbus.datastore import (
    ModbusSequentialDataBlock, 
    ModbusServerContext,
    ModbusDeviceContext
)
from pymodbus.server import StartAsyncTcpServer

class ElectricalSimulator:
    """Simulates 3-phase electrical circuit values"""
    
    def __init__(self):
        # Operating parameters
        self.time = 0
        self.frequency = 50  # Hz (standard European frequency)
        self.phase_shift_120 = 2 * math.pi / 3  # 120 degrees in radians
        
        # Base values for simulation
        self.base_voltage = 230  # Volts per phase
        self.base_current = 10   # Amps per phase
        self.power_factor = 0.95  # Representative PF for typical loads
        
        # Energy accumulator (kWh)
        self.total_energy = 0
        self.last_time = time.time()
    
    def get_values(self):
        """Generate and return current electrical values"""
        self.time = time.time()
        # reduce numeric drift at large epoch value for better sinusoidal precision
        phase_time = (self.time % (1.0 / self.frequency)) * self.frequency
        
        # Simulate AC voltage for each phase (sinusoidal)
        voltage_l1 = self.base_voltage * math.sin(2 * math.pi * phase_time)
        voltage_l2 = self.base_voltage * math.sin(2 * math.pi * phase_time - self.phase_shift_120)
        voltage_l3 = self.base_voltage * math.sin(2 * math.pi * phase_time - 2 * self.phase_shift_120)
        
        # Neutral voltage (should be ~0 in balanced system, but add small offset for realism)
        voltage_n = (voltage_l1 + voltage_l2 + voltage_l3) / 3
        
        # Simulate AC current for each phase (with slight phase shift due to PF)
        phase_shift_pf = math.acos(self.power_factor)
        current_l1 = self.base_current * math.sin(2 * math.pi * self.frequency * self.time - phase_shift_pf)
        current_l2 = self.base_current * math.sin(2 * math.pi * self.frequency * self.time - self.phase_shift_120 - phase_shift_pf)
        current_l3 = self.base_current * math.sin(2 * math.pi * self.frequency * self.time - 2 * self.phase_shift_120 - phase_shift_pf)
        
        # Neutral current (should be ~0 in balanced system)
        current_n = current_l1 + current_l2 + current_l3
        
        # Calculate instantaneous power (P = V * I * PF)
        # Use RMS values for power calculation
        v_rms = self.base_voltage / math.sqrt(2)
        i_rms = self.base_current / math.sqrt(2)
        power_per_phase = v_rms * i_rms * self.power_factor
        total_power = power_per_phase * 3 / 1000  # Convert to kW
        
        # Update energy accumulator
        current_time = time.time()
        time_delta = current_time - self.last_time
        self.last_time = current_time
        self.total_energy += total_power * (time_delta / 3600)  # Convert to kWh
        
        return {
            'voltage_l1': abs(voltage_l1),
            'voltage_l2': abs(voltage_l2),
            'voltage_l3': abs(voltage_l3),
            'voltage_n': abs(voltage_n),
            'current_l1': abs(current_l1),
            'current_l2': abs(current_l2),
            'current_l3': abs(current_l3),
            'current_n': abs(current_n),
            'total_power': total_power,
            'total_energy': self.total_energy
        }


def float_to_registers(value):
    """Convert a Python float to two Modbus 16-bit registers (IEEE 754)"""
    float_bytes = struct.pack('>f', value)
    return struct.unpack('>HH', float_bytes)


async def update_registers_async(context, simulator, update_interval=0.5):
    """Periodically update holding registers with simulated values"""
    while True:
        try:
            values = simulator.get_values()
            
            # Register addresses start at 1000
            register_index = 0
            
            # Each float value occupies 2 registers
            for key in ['voltage_l1', 'voltage_l2', 'voltage_l3', 'voltage_n',
                       'current_l1', 'current_l2', 'current_l3', 'current_n',
                       'total_power', 'total_energy']:
                
                reg_high, reg_low = float_to_registers(values[key])
                context[0x01].setValues(3, 1000 + register_index, [reg_high, reg_low])
                register_index += 2
            
            await asyncio.sleep(update_interval)
        except Exception as e:
            print(f"Error updating registers: {e}")
            await asyncio.sleep(update_interval)


async def run_server_async():
    """Start the Modbus TCP server (async version for pymodbus v3)"""
    
    # Create data blocks for each register type
    # In pymodbus v3, we need separate blocks for DO (discrete outputs), DI (discrete inputs),
    # CO (coils), and HR (holding registers) / IR (input registers)
    holding_registers = ModbusSequentialDataBlock(0, [0] * 2000)
    
    # Create a device context for slave 0
    slave_context = ModbusDeviceContext(
        di=ModbusSequentialDataBlock(0, [0] * 2000),  # Discrete inputs
        co=ModbusSequentialDataBlock(0, [0] * 2000),  # Coils
        hr=holding_registers,                          # Holding registers
        ir=ModbusSequentialDataBlock(0, [0] * 2000),  # Input registers
    )
    
    # Create server context with slave 1 as device ID 1 (standard Modbus default)
    context = ModbusServerContext(devices={0x01: slave_context}, single=False)
    
    # Create simulator
    simulator = ElectricalSimulator()
    
    print("Starting Modbus TCP Server on localhost:5023")
    print("Holding Registers: 1000-1019 (10 float values × 2 registers each)")
    print("Values: V_L1, V_L2, V_L3, V_N, I_L1, I_L2, I_L3, I_N, Power, Energy")
    print("Press Ctrl+C to stop...\n")
    
    # Create tasks for server and register updates
    try:
        # IMPORTANT: Using port 5023 to avoid admin privileges requirement and conflicts
        server_task = asyncio.create_task(
            StartAsyncTcpServer(context, address=("127.0.0.1", 5023))
        )

        # Use a non-round multiple of 50Hz to avoid repeated fixed-phase sampling
        update_interval = 0.123
        update_task = asyncio.create_task(
            update_registers_async(context, simulator, update_interval)
        )

        # Wait for both tasks (server runs indefinitely until cancelled)
        await asyncio.gather(server_task, update_task)
    except KeyboardInterrupt:
        print("\nServer stopped.")
    except PermissionError as e:
        print(f"PermissionError: {e}")
        print("Try using a port number > 1024")


def run_server():
    """Entry point that runs the async server"""
    try:
        asyncio.run(run_server_async())
    except KeyboardInterrupt:
        print("\nServer shutdown.")


if __name__ == '__main__':
    run_server()
