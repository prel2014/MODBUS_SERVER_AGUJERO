import json

from pymodbus.payload import BinaryPayloadBuilder,BinaryPayloadDecoder
from pymodbus.device import ModbusDeviceIdentification
from pymodbus.constants import Endian
from pymodbus.datastore import (
    ModbusSequentialDataBlock,
    ModbusServerContext,
    ModbusSlaveContext,
)
import sqlite3 as sql
from src.config_registros_IMG_AGUJERO import Imagen_Agujeros
class modbus_server_config:
    def __init__(self,p_modbus) -> None:
        self.context:ModbusServerContext
        self.ip_address=(p_modbus[0],p_modbus[1])
        self.identity=ModbusDeviceIdentification(info_name=p_modbus[2])
        self.ir_address=p_modbus[3]
        self.hr_address=p_modbus[4]
        self.ir_count:int
        self.hr_count:int
class DB_config:
    def __init__(self,p_db) -> None:
        self.db_brazo_ir=p_db[0]
        self.db_brazo_hr=p_db[1]
        self.table_brazo_ir=p_db[2]
        self.table_brazo_hr=p_db[3] 

class Config_server_db_brazos:
            
    def __init__(self,config_file="Parametros/imagen_agujero.json") -> None:
        self.archivo_path=config_file
        p_modbus,p_db=self.leer_parametros(self.archivo_path)
        self.modbus=modbus_server_config(p_modbus)
        self.db_sql=DB_config(p_db)

        self.Brazo1=Imagen_Agujeros(
            ir_database=self.db_sql.db_brazo_ir,
            hr_database=self.db_sql.db_brazo_hr,
            ir_table=self.db_sql.table_brazo_ir,
            hr_table=self.db_sql.table_brazo_hr
            )
    
    def leer_parametros(self,archivo_path):
        f=open(archivo_path,'r')
        parametros = json.load(f)
        modbus=parametros['modbus']
        p_modbus=(modbus['ip'],modbus['port'],modbus['info_name'],modbus['ir_address'],modbus['hr_address'])

        db=parametros['registro']
        p_db=(db['db_ir'],db['db_hr'],db['table_ir'],db['table_hr'])

        return p_modbus,p_db

    def init_database(self):
        self.Brazo1.Registro_input.db_control.CreateTable()
        self.Brazo1.Registro_holding.db_control.CreateTable()
    
    def setup_modbus_ir_block(self):
        builder = BinaryPayloadBuilder(
            byteorder=Endian.BIG, 
            wordorder=Endian.LITTLE)

        self.Brazo1.Registro_input.modbus_config.modbus_create_register(builder)
        self.modbus.ir_count=len(builder.to_registers())

        block = ModbusSequentialDataBlock(self.modbus.ir_address, builder.to_registers())
        return block

    def setup_modbus_hr_block(self):
        builder = BinaryPayloadBuilder(
            byteorder=Endian.BIG, 
            wordorder=Endian.LITTLE)

        self.Brazo1.Registro_holding.modbus_config.modbus_create_register(builder)
        self.modbus.hr_count=len(builder.to_registers())

        block = ModbusSequentialDataBlock(self.modbus.hr_address, builder.to_registers())
        return block

    def setup_modbus_server(self,arg:modbus_server_config):
        datablock_hr=self.setup_modbus_hr_block()
        datablock_ir=self.setup_modbus_ir_block()
        context = ModbusSlaveContext(di=None, co=None, hr=datablock_hr, ir=datablock_ir, zero_mode=True)
        arg.context= ModbusServerContext(slaves=context, single=True)
        print(f"servidor modbus con cantidad ir:{self.modbus.ir_count}-hr:{self.modbus.hr_count}")
        #self.modbus.context = ModbusServerContext(slaves=context, single=True)

    def update_input_register_data(self,data):

        #self.Brazo1.Registro_input.db_read_values_update()
        self.Brazo1.Registro_input.update_variables(data)

        builder = BinaryPayloadBuilder(
            byteorder=Endian.BIG, 
            wordorder=Endian.LITTLE)
        self.Brazo1.Registro_input.modbus_write_register_values(builder)
        payload = builder.to_registers()
        return payload
    
    def read_modbus_holding_regiser(self,payload):
        decoder=BinaryPayloadDecoder.fromRegisters(
            registers=payload,
            byteorder=Endian.BIG,
            wordorder=Endian.LITTLE)
        self.Brazo1.Registro_holding.modbus_decode_register_values(decoder)

        self.Brazo1.Registro_holding.update_row_data()
    
if __name__ == "__main__":
    entorno=Config_server_db_brazos()