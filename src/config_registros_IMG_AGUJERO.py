from pymodbus.constants import Endian
from pymodbus.datastore import ModbusServerContext
from pymodbus.device import ModbusDeviceIdentification
from pymodbus.payload import BinaryPayloadBuilder,BinaryPayloadDecoder

from src.database import Database_Control
from src.database import SQL_config

class Imagen_Agujeros:
    class Input_register:
        class modbus_config:
            def __init__(self) -> None:
                self.fc_as_hex=0x04
                
            def modbus_create_register(builder:BinaryPayloadBuilder):
                builder.add_16bit_uint(1)
                builder.add_16bit_uint(2)
                builder.add_16bit_uint(3)   
                builder.add_32bit_float(4.1)
                builder.add_32bit_float(5.1)
                builder.add_16bit_uint(6) 
                builder.add_32bit_float(7.1)
                builder.add_32bit_float(8.1)

            def modbus_create_register2(builder:BinaryPayloadBuilder,data:tuple):
                builder.add_16bit_uint(data[0])
                builder.add_16bit_uint(data[1])
                builder.add_16bit_uint(data[2])   
                builder.add_32bit_float(data[3])
                builder.add_32bit_float(data[4])
                builder.add_16bit_uint(data[5]) 
                builder.add_32bit_float(data[6])
                builder.add_32bit_float(data[7])
    
        def __init__(self,database="brazo1.db",table="Input_register",address=0x00):
            self.address=address

            row_config=["status, cod_falla, R_X, R_Y,R_Z,R_ROLL,R_PITCH,R_YAW,Zonas",
                        "?,?,?,?,?,?,?,?,?"]
            table_create_instruction="""CREATE TABLE IF NOT EXISTS {}(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                status INTEGER NOT NULL,
                cod_falla INTEGER NOT NULL,
                R_X FLOAT NOT NULL,
                R_Y FLOAT NOT NULL,
                R_Z FLOAT NOT NULL,
                R_ROLL FLOAT NOT NULL,
                R_PITCH FLOAT NOT NULL,
                R_YAW FLOAT NOT NULL,
                Zonas INTEGER NOT NULL,
                hora TIMESTAMP DEFAULT (strftime('%Y-%m-%d %H:%M:%f', 'now', 'localtime'))
            )""".format(table)

            self.config_SQL=SQL_config(database=database,tablename=table,row_config=row_config,table_create_instruction=table_create_instruction)
            self.db_control=Database_Control(self.config_SQL)

            self.status:int=0     
            self.agujero:int=0
            self.falla:int=0
            self.coor_carril:float=0.0
            self.coor_lev_X:float=0.0
            self.chequeo:int=0
            self.coor_carril_ref:float=0.0
            self.coor_lev_X_ref:float=0.0  

            self.row_data=(self.status,self.agujero,self.falla,self.coor_carril,self.coor_lev_X,self.chequeo,self.coor_carril_ref,self.coor_lev_X_ref)
        
        def update_row_data(self):
            self.row_data=(self.status,self.agujero,self.falla,self.coor_carril,self.coor_lev_X,self.chequeo,self.coor_carril_ref,self.coor_lev_X_ref)
        
        def update_list_data(self):
            lista=[0,self.status,self.agujero,self.falla,self.coor_carril,self.coor_lev_X,self.chequeo,self.coor_carril_ref,self.coor_lev_X_ref]
            return lista
            
        def update_variables(self,data:tuple):
            self.status=data[1]
            self.agujero=data[2]
            self.falla=data[3]
            self.coor_carril=data[4]
            self.coor_lev_X=data[5]
            self.chequeo=data[6]
            self.coor_carril_ref=data[7]
            self.coor_lev_X_ref=data[8]
        
        def modbus_write_register_values(self,builder:BinaryPayloadBuilder):
            builder.add_16bit_uint(self.status)
            builder.add_16bit_uint(self.agujero)
            builder.add_16bit_uint(self.falla)   
            builder.add_32bit_float(self.coor_carril)
            builder.add_32bit_float(self.coor_lev_X)
            builder.add_16bit_uint(self.chequeo) 
            builder.add_32bit_float(self.coor_carril_ref)
            builder.add_32bit_float(self.coor_lev_X_ref)       
        
        def db_read_values_update(self):
            data=self.db_control.ReadLastRows()
            self.update_variables(data=data)

    class Holding_register:
        class modbus_config:
            def __init__(self) -> None:
                self.fc_as_hex=0x03
                
            def modbus_create_register(builder:BinaryPayloadBuilder):
                builder.add_16bit_uint(1)
                builder.add_16bit_uint(1)
                builder.add_16bit_uint(3)
                builder.add_32bit_float(4.1)    
                builder.add_32bit_float(5.1)

            def modbus_create_register2(builder:BinaryPayloadBuilder,data:tuple):
                builder.add_16bit_uint(data[0])
                builder.add_16bit_uint(data[1])
                builder.add_16bit_uint(data[2])
                builder.add_32bit_float(data[3])    
                builder.add_32bit_float(data[4])
        
        def __init__(self,database="brazo1.db",table="Holding_register",address=0x00):
            self.address=address

            row_config=["control_brazo, config_homing, modo, movimiento, mov_1, mov_2, mov_3, mov_4, mov_5, mov_6"
                        ,"?,?,?,?,?,?,?,?,?,?"]
            table_create_instruction="""CREATE TABLE IF NOT EXISTS {}(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                control_brazo INTEGER,
                config_homing INTEGER,
                modo INTEGER,
                movimiento INTEGER,
                mov_1 FLOAT,
                mov_2 FLOAT,
                mov_3 FLOAT,
                mov_4 FLOAT,
                mov_5 FLOAT,
                mov_6 FLOAT,
                hora TIMESTAMP DEFAULT (strftime('%Y-%m-%d %H:%M:%f', 'now', 'localtime'))
            )""".format(table)

            self.config_SQL=SQL_config(database=database,tablename=table,row_config=row_config,table_create_instruction=table_create_instruction)
            self.db_control=Database_Control(self.config_SQL)

            self.id:int=0     
            self.control:int=2
            self.ind_agujero:int=0
            self.coor_carril_ref:float=0.0
            self.coor_lev_X_ref:float=0.0


            self.row_data=(self.id,self.control,self.ind_agujero,self.coor_carril_ref,self.coor_lev_X_ref)

        def update_row_data(self):
            self.row_data=(self.id,self.control,self.ind_agujero,self.coor_carril_ref,self.coor_lev_X_ref)
            
        def update_list_data(self):
            lista=[self.id,self.control,self.ind_agujero,self.coor_carril_ref,self.coor_lev_X_ref]
            return lista
            
        def update_variables(self,data:tuple):
            self.id=data[1]
            self.control=data[2]
            self.ind_agujero=data[3]
            self.coor_carril_ref=data[4]
            self.coor_lev_X_ref=data[5]
            
        def update_variables2(self,data:tuple):
            self.id=data[0]
            self.control=data[1]
            self.ind_agujero=data[2]
            self.coor_carril_ref=data[3]
            self.coor_lev_X_ref=data[4]

        def modbus_load_register_values(self,builder:BinaryPayloadBuilder):
            builder.add_16bit_uint(self.id)
            builder.add_16bit_uint(self.control)
            builder.add_16bit_uint(self.ind_agujero)
            builder.add_32bit_float(self.coor_carril_ref)    
            builder.add_32bit_float(self.coor_lev_X_ref)
        
        def modbus_decode_register_values(self,decoder:BinaryPayloadDecoder):
            self.id=decoder.decode_16bit_uint()
            self.control=decoder.decode_16bit_uint()
            self.ind_agujero=decoder.decode_16bit_uint()
            self.coor_carril_ref=decoder.decode_32bit_float()    
            self.coor_lev_X_ref=decoder.decode_32bit_float()

        def db_read_values_update(self):
            data=self.db_control.ReadLastRows()
            self.update_variables(data=data)

    def __init__(self,ir_database="brazo.db",ir_table="Input_register",hr_database="brazo.db",hr_table="Holding_register") -> None:
        self.Registro_input=self.Input_register(database=ir_database,table=ir_table,address=0x00)
        self.Registro_holding=self.Holding_register(database=hr_database,table=hr_table,address=0x00)
