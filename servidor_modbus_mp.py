#!/usr/bin/env python3

from pymodbus.server import StartAsyncTcpServer
import asyncio
from datetime import datetime
from multiprocessing.managers import ListProxy

from src.entorno_IMG_AGUJERO import Config_server_db_brazos,modbus_server_config


LINE_CLEAR = '\x1b[2K'
LINE_UP_1 = '\033[1A'
LINE_UP_3 = '\033[3A'
LINE_DOWN_1 = '\033[1B'
LINE_RETURN='\r'
LINE_FORMWARE='\033[20C'

class Exchange_data:
    def __init__(self) -> None:
        self.data_read:ListProxy
        self.data_write:ListProxy
        self.debug:bool
        self.entorno_interno:Config_server_db_brazos
        self.context_modbus:modbus_server_config

data_exhange=Exchange_data()
entorno_2=Config_server_db_brazos()
data_exhange.entorno_interno=entorno_2
entorno=data_exhange.entorno_interno
context_act=entorno.modbus

def update_entorno():
    entorno2=data_exhange.entorno_interno
    context_act=data_exhange.entorno_interno.modbus
    print(f"Modbus Archivo parametros: {entorno2.archivo_path}")
    return (entorno2,context_act)

async def run_async_server(arg:modbus_server_config):
    txt = f"### start MODBUS ASYNC server, listening on {arg.ip_address[0]} - port:{arg.ip_address[1]}"
    print(txt)
    server = await StartAsyncTcpServer(
    context=arg.context,  # Data storage
    identity=arg.identity,  # server identify
    address=arg.ip_address,  # listen address
    # custom_functions=[],  # allow custom handling
    # framer=args.framer,  # The framer strategy to use
    # ignore_missing_slaves=True,  # ignore request to a missing slave
    # broadcast_enable=False,  # treat slave_id 0 as broadcast address,
    # timeout=1,  # waiting time for request to complete
    # TBD strict=True,  # use strict timing, t1.5 for Modbus RTU
    )
    return server

def update_modbus_input_register(arg:modbus_server_config,data):
    payload=entorno.update_input_register_data(data)
    arg.context[0].setValues(0x04, arg.ir_address, payload)

def read_modbus_holding_regiser(arg:modbus_server_config):
    count = arg.hr_count
    values = arg.context[0].getValues(0x03, arg.hr_address, count=count)

    entorno.read_modbus_holding_regiser(values)
    variable=entorno.Brazo1.Registro_holding.update_list_data()

    return variable

async def updating_task_PROCESS(arg:modbus_server_config,debug=False):

    txt = (
        f"MODBUS:updating_task: started: initialised"
    )
    print(txt)
   
    while True:
        try:
            #start = datetime.now()
            #time_taken2 = end2 - start

            data=data_exhange.data_read[0]
           
            update_modbus_input_register(arg,data)
            
            varaible=read_modbus_holding_regiser(arg)
            data_exhange.data_write[0]=varaible

            #end = datetime.now()
            #time_taken = end - start
            #await rate.sleep()
            
            if(debug):
                print("Updating IR:{}".format(data))
                print(f"Reading HR:{data_exhange.data_write[0]}")
                #print('Time Ciclo: {} \tTime Pros: {}'.format(time_taken2.microseconds, time_taken.microseconds))
                #print('Modbus Time Ciclo: {}'.format(time_taken2.microseconds),end=LINE_RETURN)
                #print('\033[30C Time Pros: {}'.format(time_taken.microseconds))
            
            await asyncio.sleep(0.01)
            #end2 = datetime.now()
            if(debug):
                print(LINE_UP_1,end=LINE_CLEAR)
                print(LINE_UP_1,end=LINE_CLEAR)
                #print(LINE_UP_1,end=LINE_CLEAR)
        except KeyboardInterrupt:
            print("MODBUS SERVER Terminado")
            break
        except Exception as error:
            print("MODBUS SERVER ERROR: ",type(error).__name__)
            break
            
async def run_updating_server_mp(entorno_int:Config_server_db_brazos):
    """Start updating_task concurrently with the current task."""
    try:
        task = asyncio.create_task(updating_task_PROCESS(arg=context_act,debug=data_exhange.debug))
        task.set_name("example updating task")
        await run_async_server(context_act)  # start the server
        task.cancel()
    except KeyboardInterrupt:
        print("modbus run task Terminado")
        task.cancel()
    except:
        print("modbus run task ERROR")
        task.cancel()

async def main_mp(entorno_int:Config_server_db_brazos):
    """Combine setup and run."""
    try:
        entorno.setup_modbus_server(context_act)
        await run_updating_server_mp(entorno_int)
    except KeyboardInterrupt:
        print("modbus Main Terminado")
        
    except:
        print("Modbus Main Error")

def run_main_async(list_ir:ListProxy,list_hr:ListProxy,debug:bool=False,entorno_int:Config_server_db_brazos=entorno_2):
    """Para multiprocess Corre el programa del servidor MODBUS async.
    :param list_ir: a ListProxy lista compartida que comparte la informacion del registro IR entre los procesos
    :param list_hr: a ListProxy lista compartida que comparte la informacion del registro HR entre los procesos
    :param debug: a Bool activa el debugging para observar los valores de los registro IR Y HR con el fin de verificar el intercambio de data
    :param entorno_int: a Config_server_db_brazos class que contiene toda la informacion del entorno de trabajo a configurar
    """
    global entorno
    global context_act

    data_exhange.data_read=list_ir
    data_exhange.data_write=list_hr
    data_exhange.debug=debug
    data_exhange.entorno_interno=entorno_int
    data_exhange.context_modbus=entorno_int.modbus
    (entorno,context_act)=update_entorno()
    print("MODBUS SERVER trabajando")
    asyncio.run(main_mp(entorno_int), debug=True)