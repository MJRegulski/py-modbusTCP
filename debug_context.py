from pymodbus.datastore import ModbusServerContext, ModbusDeviceContext, ModbusSequentialDataBlock

hr=ModbusSequentialDataBlock(0,[0]*2000)
dc=ModbusDeviceContext(di=ModbusSequentialDataBlock(0,[0]*2000),co=ModbusSequentialDataBlock(0,[0]*2000),hr=hr,ir=ModbusSequentialDataBlock(0,[0]*2000))
ctx=ModbusServerContext(devices={0x00:dc}, single=False)
print('dc initial',dc.getValues(3,1000,2))
dc.setValues(3,1000,[171,205])
print('dc after',dc.getValues(3,1000,2))
print('ctx before',ctx[0x00].getValues(3,1000,2))
ctx[0x00].setValues(3,1000,[171,205])
print('ctx after',ctx[0x00].getValues(3,1000,2))
