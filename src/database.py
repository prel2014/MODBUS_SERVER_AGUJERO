import sqlite3 as sql

class SQL_config:
    def __init__(self,database:str,tablename:str,row_config:list,table_create_instruction:str) -> None:
        self.database_name=database
        self.table_name=tablename
        self.row_config=row_config
        self.table_create_instruction=table_create_instruction

class Database_Control:
    def __init__(self,config_SQL:SQL_config) -> None:
        self.database=config_SQL.database_name
        self.table=config_SQL.table_name
        self.row_config=config_SQL.row_config
        self.table_instruction=config_SQL.table_create_instruction
        
    def conexion(self):
        conn=sql.connect(database=self.database,isolation_level=None)
        return conn
    
    def configuracion(self,cur:sql.Cursor):
        cur.execute('pragma journal_mode = WAL')
        cur.execute('pragma synchronous = normal')
        cur.execute('pragma journal_size_limit = 6144000')
    
    def CreateDB(self):
        conn=self.conexion()
        conn.commit()
        conn.close()

    def CreateTable(self):
        conn=self.conexion()
        cursor=conn.cursor()
        self.configuracion(cursor)

        cursor.execute(self.table_instruction)
        conn.commit()

        cursor.close()
        conn.close()
    
    def load_row_data(self,data:tuple):
        self.row_data=data

    def insertRow(self,data:tuple):
        conn=self.conexion()
        cursor=conn.cursor()
        self.configuracion(cursor)

        table_variables=self.row_config
        instruccion=f"INSERT INTO {self.table}({table_variables[0]}) VALUES ({table_variables[1]})"
        datain=data
        cursor.execute(instruccion,datain)
        conn.commit()

        cursor.close()
        conn.close()
    
    def ReadLastRows(self):
        conn=self.conexion()
        cursor=conn.cursor()
        self.configuracion(cursor)
        
        instruccion=f"SELECT * FROM '{self.table}' ORDER BY id DESC LIMIT 1;"
        cursor.execute(instruccion)
        datos=cursor.fetchall()

        cursor.close()
        conn.close()

        return datos[0]
    
    def Read_write(self,data:tuple):
        conn=self.conexion()
        cursor=conn.cursor()
        self.configuracion(cursor)

        table_variables=self.row_config
        
        instruccion=f"INSERT INTO {self.table}({table_variables[0]}) VALUES ({table_variables[1]})"
        datain=data
        cursor.execute(instruccion,datain)

        instruccion2=f"SELECT * FROM '{self.table}' ORDER BY id DESC LIMIT 1;"
        cursor.execute(instruccion2)
        datosout=cursor.fetchall()
        conn.commit()

        cursor.close()
        conn.close()
        return datosout[0]
    
class Database_general:
    def __init__(self,config_SQL:SQL_config) -> None:
        self.database=config_SQL.database_name
        self.table=config_SQL.table_name
        self.row_config=config_SQL.row_config
        self.table_instruction=config_SQL.table_create_instruction

    def conexion(self):
        conn=sql.connect(database=self.database,isolation_level=None)
        return conn
    
    def configuracion(self,cur:sql.Cursor):
        cur.execute('pragma journal_mode = WAL')
        cur.execute('pragma synchronous = normal')
        cur.execute('pragma journal_size_limit = 6144000')

    def insertRow(self,data:tuple):
        conn=self.conexion()
        cursor=conn.cursor()
        self.configuracion(cursor)

        table_variables1=self.row_config
        table_variables2=self.row_config
        table_variables3=self.row_config
        instruccion=f"INSERT INTO {self.table}({table_variables1[0]}) VALUES ({table_variables1[1]})"
        datain=data
        cursor.execute(instruccion,datain)



        
        conn.commit()

        cursor.close()
        conn.close()