import random
import time
from datetime import datetime
from src.entorno_IMG_AGUJERO import Config_server_db_brazos
import numpy as np
from multiprocessing.managers import ListProxy
import json
import torch
from ultralytics import YOLO
import os
import pickle
from PIL import Image
from ultralytics.utils.ops import scale_image
import pickle
import cv2

cameraMatrix, dist = pickle.load(open( "calibration.pkl", "rb" ))
def predict_on_image(model, img, conf):
    result = model(img, conf=conf)[0]
    cls = result.boxes.cls.cpu().numpy()
    probs = result.boxes.conf.cpu().numpy()
    boxes = result.boxes.xyxy.cpu().numpy()
    if result.masks != None:
        masks = result.masks.data.cpu().numpy()
        masks = np.moveaxis(masks, 0, -1)
        h, w, c = masks.shape
        scaled_masks = scale_image(masks, result.masks.orig_shape)
        if isinstance(scaled_masks, tuple):
            masks = scaled_masks[0]
        else:
            masks = scaled_masks
        masks = np.moveaxis(masks, -1, 0)
    else:
        masks=[]
    return boxes, masks, cls, probs


def overlay(image, mask, color, alpha, resize=None):
    color = color[::-1]
    colored_mask = np.expand_dims(mask, 0).repeat(3, axis=0)
    colored_mask = np.moveaxis(colored_mask, 0, -1)
    masked = np.ma.MaskedArray(image, mask=colored_mask, fill_value=color)
    image_overlay = masked.filled()
    if resize is not None:
        image = cv2.resize(image.transpose(1, 2, 0), resize)
        image_overlay = cv2.resize(image_overlay.transpose(1, 2, 0), resize)
    image_combined = cv2.addWeighted(image, 1 - alpha, image_overlay, alpha, 0)
    return image_combined

def correction_of_image(img,cameraMatrix,dist):
    h,  w = img.shape[:2]
    newCameraMatrix, roi = cv2.getOptimalNewCameraMatrix(cameraMatrix, dist, (w,h), 1, (w,h))
    undistorted = cv2.undistort(img, cameraMatrix, dist, None, newCameraMatrix)
    x, y, w, h = roi
    undistorted = undistorted[y:y+h, x:x+w]
    return undistorted

def pixels2cm(point,fx,fy):
    x=point[0]*fx
    y=point[1]*fy
    return [x,y]
entorno=Config_server_db_brazos()
Variable_IR=entorno.Brazo1.Registro_input
Variable_HR=entorno.Brazo1.Registro_holding

LINE_CLEAR = '\x1b[2K'
LINE_UP_1 = '\033[1A'
LINE_UP_3 = '\033[3A'
LINE_UP_4 = '\033[4A'
LINE_DOWN_1 = '\033[1B'
LINE_DOWN_4 = '\033[4B'
LINE_RETURN='\r'
LINE_FORMWARE='\033[20C'

class SIM_agujero:
    def __init__(self) -> None:
            self.Pos_carril:float=0.0
            self.Pos_lev_X:float=0.0

            self.Local_carril:list=[0]
            self.Local_lev_X:list=[0]

            self.t_0_0:datetime
            self.t_0_1:datetime

            self.has_data:bool=False

class Variables_Control:
    class Status:
        def __init__(self) -> None:
            self.status_word:int=0

            self.verificador:bool   =False
            self.libre:bool         =False
            self.trabajando:bool    =False
            self.terminado:bool     =False
            self.falla:bool         =False
            self.modo_lectura:bool  =False

        def set_libre(self):
            if not self.falla:
                self.libre      =True
                self.trabajando =False
                self.terminado  =False
        def set_trabajando(self):
            if not self.falla:
                self.libre      =False
                self.trabajando =True
                self.terminado  =False
        def set_terminado(self):
            if not self.falla:
                self.libre      =False
                self.trabajando =False
                self.terminado  =True
        def set_fallo(self):
            self.libre      =False
            self.trabajando =False
            self.terminado  =False
            self.falla      =True
        def caso_reset(self):
            self.libre      =False
            self.trabajando =False
            self.terminado  =False
            self.falla      =False
        def set_lectuta(self):
            self.modo_lectura=True
    class Control:
        def __init__(self) -> None:
            self.control_word:int=0

            self.verificador:bool=False
            self.iniciar:bool=False
            self.reset:bool=False
            self.leer_Data:bool=False
            self.update_ref:bool=False
    class Falla_code:
        def __init__(self) -> None:
            self.falla_word:int=0

            self.err_agujero:bool=False
            self.err_no_data:bool=False
        
        def reset_falla(self):
            self.err_agujero=False
            self.err_no_data=False

    def __init__(self) -> None:
        self.estado =self.Status()
        self.control=self.Control()
        self.fallo  =self.Falla_code()

        self.json_file:dict

        self.ref_carril:float=0.0
        self.ref_lev_x:float=0.0

        self.flag_calculado:bool=False
        self.flag_procesando:bool=False
        self.flag_actualizar:bool=False

        self.leer_referencias()
    
    def leer_referencias(self):
        with open("Parametros/imagen_referencias.json") as f:
            parametros = json.load(f)
        self.json_file=parametros
        referencia=parametros['referencias']

        self.ref_carril=referencia['carril']
        self.ref_lev_x=referencia['lev_x']
        #print(f"ref carril: {self.ref_carril}")
        #print(f"ref lev_x: {self.ref_lev_x}")
    
    def escribir_referencia(self):
        with open("Parametros/imagen_referencias.json",'w') as archivo_nuevo:
            json.dump(self.json_file, archivo_nuevo)

    def update_status_WORD(self):
        self.estado.verificador=True
        b0=self.estado.verificador
        b1=self.estado.libre
        b2=self.estado.trabajando
        b3=self.estado.terminado
        b4=self.estado.falla
        b5=self.estado.modo_lectura
        b6=False
        b7=False
        b8=False
        b9=False
        b10=False
        b11=False
        b12=False
        b13=False
        b14=False
        b15=False

        array_bool=[
            b0, 
            b1, 
            b2, 
            b3, 
            b4, 
            b5, 
            b6, 
            b7, 
            b8, 
            b9, 
            b10,
            b11,
            b12,
            b13,
            b14,
            b15
        ]

        self.estado.status_word=self.convert_bool_array_to__word(array_bool)

    def update_fallo_WORD(self):
        
        b0=True
        b1=self.fallo.err_agujero
        b2=self.fallo.err_no_data
        b3=False
        b4=False
        b5=False
        b6=False
        b7=False
        b8=False
        b9=False
        b10=False
        b11=False
        b12=False
        b13=False
        b14=False
        b15=False

        array_bool=[
            b0, 
            b1, 
            b2, 
            b3, 
            b4, 
            b5, 
            b6, 
            b7, 
            b8, 
            b9, 
            b10,
            b11,
            b12,
            b13,
            b14,
            b15
        ]

        self.fallo.falla_word=self.convert_bool_array_to__word(array_bool)

    def caso_reset(self):
        if self.control.reset:
            self.estado.set_libre()
            self.fallo.reset_falla()
            self.flag_calculado=False
            self.flag_procesando=False

    def update_control(self,control_word:int):
        self.control.control_word=control_word
        b_array=self.convert_word_to_bool_array(control_word)
        self.control.verificador=   b_array[0]
        self.control.iniciar=       b_array[1]
        self.control.reset=         b_array[2]
        self.control.leer_Data=     b_array[3]
        self.control.update_ref=    b_array[4]
        #print(self.control.control_word)

    def convert_word_to_bool_array(self,word:int):
        b0  =bool(word&1)
        b1  =bool(word&2)
        b2  =bool(word&4)
        b3  =bool(word&8)
        b4  =bool(word&16)
        b5  =bool(word&32)
        b6  =bool(word&64)
        b7  =bool(word&128)
        b8  =bool(word&256)
        b9  =bool(word&512)
        b10 =bool(word&1024)
        b11 =bool(word&2048)
        b12 =bool(word&4096)
        b13 =bool(word&8192)
        b14 =bool(word&16384)
        b15 =bool(word&32768)
        array_bool=[
            b0, 
            b1, 
            b2, 
            b3, 
            b4, 
            b5, 
            b6, 
            b7, 
            b8, 
            b9, 
            b10,
            b11,
            b12,
            b13,
            b14,
            b15
        ]
        #print(f"CONTROL ARRAY:{array_bool}")
        return array_bool

    def convert_bool_array_to__word(self,array_bool:list):
        mult=[1,2,4,8,16,32,64,128,256,512,1024,2048,4096,8192,16384,32768]
        bit=array_bool
        data=[0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]

        for i in range(len(bit)):
            data[i]=mult[i]*bit[i]
        w0=sum(data)

        #print(f"STATUS WORD:{w0}")
        return w0

varaible=Variables_Control()
proc_agu=SIM_agujero()

def update_referencia():
    if varaible.control.update_ref:
        if not varaible.flag_actualizar:
            varaible.ref_carril=Variable_HR.coor_carril_ref
            varaible.ref_lev_x=Variable_HR.coor_lev_X_ref

            varaible.json_file['referencias']['carril']=varaible.ref_carril
            varaible.json_file['referencias']['lev_x']=varaible.ref_lev_x
            varaible.escribir_referencia()

            Variable_IR.coor_carril_ref=varaible.ref_carril
            Variable_IR.coor_lev_X_ref=varaible.ref_lev_x

            varaible.flag_actualizar=True
    else:
        varaible.flag_actualizar=False

def coodenadas_locales(model,cap):
    if varaible.estado.terminado and not varaible.control.iniciar:
        varaible.estado.set_libre()
        varaible.flag_procesando=False
        varaible.flag_calculado=False

    if varaible.control.iniciar and not varaible.control.reset and varaible.estado.libre:
        print ("inicio")
        varaible.estado.set_trabajando()
        varaible.flag_calculado=True
        varaible.flag_procesando=True
        proc_agu.t_0_0=datetime.now()

    if varaible.flag_calculado:
        print("calculando")
        holes=[]
        local_carril=[]
        local_lev_x=[]
        sep_x=45.0
        sep_y=45.0
        if cap.isOpened():
            ret,img = cap.read()
            undistorted = correction_of_image(img,cameraMatrix,dist)
            boxes, masks, cls, probs = predict_on_image(model, undistorted, conf=0.7)
            cx=0
            cy=0
            for i,mask_i in enumerate(masks):
                m=(255*mask_i).astype(np.uint8)
                contours,_ = cv2.findContours(mask_i.astype(np.uint8),cv2.RETR_TREE,cv2.CHAIN_APPROX_SIMPLE)
                if contours:
                    momentos = cv2.moments(contours[0])
                    if momentos["m00"] != 0:
                        cx=int(momentos["m10"]/momentos["m00"])
                        cy=int(momentos["m01"]/momentos["m00"])
                    else:
                        cx=0
                        cy=0
                x,y = pixels2cm([cx,cy],1.125*2.5/164,1.125*2.5/166)
                x=round(x,1)
                y=round(y,1)
                local_carril.append(y+sep_y)
                local_lev_x.append(x+sep_x)

        proc_agu.Local_carril =local_carril
        proc_agu.Local_lev_X  =local_lev_x
        varaible.flag_calculado=False
        proc_agu.has_data=True
    
    if varaible.flag_procesando:
        proc_agu.t_0_1=datetime.now()
        time_Delta=proc_agu.t_0_1-proc_agu.t_0_0
        #print(f"time total:{time_Delta}, init:{proc_agu.t_0_0}")

        if time_Delta.seconds>=1 and varaible.estado.trabajando:
            #print(f"termino ya: {time_Delta.microseconds}")
            varaible.estado.set_terminado()
            varaible.flag_procesando=False
        
def consulta_agujero():
    n_agujero=Variable_HR.ind_agujero
    if varaible.control.leer_Data:
        varaible.estado.set_lectuta()
        if proc_agu.has_data:
            if n_agujero>=0 and n_agujero<=71:
                proc_agu.Pos_carril =varaible.ref_carril    +   proc_agu.Local_carril[n_agujero]
                proc_agu.Pos_lev_X  =varaible.ref_lev_x     +   proc_agu.Local_lev_X[n_agujero]
                #print(f"Local carril:{proc_agu.Local_carril[n_agujero]}")
                #print(f"Local lev_X:{proc_agu.Local_lev_X[n_agujero]}")

                Variable_IR.coor_carril=proc_agu.Pos_carril
                Variable_IR.coor_lev_X=proc_agu.Pos_lev_X
                Variable_IR.agujero=Variable_HR.ind_agujero
                Variable_IR.chequeo=Variable_IR.agujero
            else:
                #print("falla agujero")
                varaible.fallo.err_agujero=True
        else:
            varaible.fallo.err_no_data=True
    else:
        varaible.estado.modo_lectura=False

def reset_estado():
    if varaible.control.reset:
        varaible.caso_reset()

def main(list_ir:ListProxy,list_hr:ListProxy,debug=False):
    print("control_br activo")
    data_cero=(0,0,0,0,0)

    Variable_HR.update_variables2(data_cero)
    varaible.estado.set_libre()
    Variable_IR.coor_carril_ref=varaible.ref_carril
    Variable_IR.coor_lev_X_ref=varaible.ref_lev_x
    model = YOLO('conos.pt')
    model.to("cuda") 
    cap=cv2.VideoCapture(4)
    cap.set(3,3264)
    cap.set(4,2448)
    while True:
        try:
            #start = datetime.now()
            
            ###Lectura de registro HR
            data_hr=list_hr[0]
            Variable_HR.update_variables2(tuple(data_hr))
            
            ###Interpretacion de registro CONTROL de HR
            varaible.update_control(Variable_HR.control)
            
            ### Codigo DETECCION
            update_referencia()

            coodenadas_locales(model,cap)
            consulta_agujero()

            reset_estado()


            
            
            ###Escritura de registro STATUS del IR
            varaible.update_status_WORD()
            varaible.update_fallo_WORD()
            Variable_IR.status=varaible.estado.status_word
            Variable_IR.falla=varaible.fallo.falla_word

            ###Escritura de registro IR
            data=Variable_IR.update_list_data()
            list_ir[0]=data

            ###debug###

            if debug:
                print(f"Data control IR:{list_ir[0]}")
                print(f"Data control HR:{data_hr}")
                print(f"Data control CARRIL:{proc_agu.Local_carril[0]}")
                print(f"Data control LEV__X:{proc_agu.Local_lev_X[0]}")

            time.sleep(0.01)
            if debug:
                print(LINE_UP_1,end=LINE_CLEAR)
                print(LINE_UP_1,end=LINE_CLEAR)
                print(LINE_UP_1,end=LINE_CLEAR)
                print(LINE_UP_1,end=LINE_CLEAR)
        except KeyboardInterrupt:
            print("Control interrumpido")
            break

        except Exception as error:
            print("Control fallo: ",type(error).__name__)
            break
        finally:
            cap.release()
            cv2.destroyAllWindows()

        #end = datetime.now()
        #time_taken = end - start
        #print('Time: ',time_taken)
