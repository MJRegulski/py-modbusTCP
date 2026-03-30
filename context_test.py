from pymodbus.datastore import ModbusServerContext, ModbusDeviceContext, ModbusSequentialDataBlock

hr = ModbusSequentialDataBlock(0, [0]*2000)
dc = ModbusDeviceContext(
    di=ModbusSequentialDataBlock(0, [0]*2000),
    co=ModbusSequentialDataBlock(0, [0]*2000),
    hr=hr,
    ir=ModbusSequentialDataBlock(0, [0]*2000),
)
ctx = ModbusServerContext(devices={0x01: dc}, single=False)
print('before', ctx[0x01].getValues(3, 1000, 2))
ctx[0x01].setValues(3, 1000, [258, 515])
print('after', ctx[0x01].getValues(3, 1000, 2))
print('hr direct', hr.getValues(3, 1000, 2))
