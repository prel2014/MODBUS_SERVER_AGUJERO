import torch
from ultralytics import YOLO
import os
import pickle
from PIL import Image
from ultralytics.utils.ops import scale_image
import pickle
import cv2
import numpy as np
import datetime
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

def main():
    holes=[]
    print(torch.cuda.is_available())
#    cap = cv2.VideoCapture("video.mp4")
#    cap.set(3,1920)
#    cap.set(4,1080)
    model = YOLO('conos.pt')
    model.to("cuda") 
    switch = True
    j=0
    cameraMatrix, dist = pickle.load(open( "calibration.pkl", "rb" ))
    folder = datetime.datetime.now().strftime("%Y-%m-%d")
    os.makedirs(f"dataset/{folder}",exist_ok=True)
    nun_muestras = len(os.listdir(f"dataset/{folder}"))
#    while cap.isOpened():
    for path in os.listdir("dataset/2024-05-10"):
#   ret,img = cap.read()
        img = cv2.imread(f"dataset/2024-05-10/{path}")
        img = cv2.resize(img,(0,0),fx=0.25,fy=0.25)
        undistorted = correction_of_image(img,cameraMatrix,dist)
        h,w,_=undistorted.shape
        if switch:
            boxes, masks, cls, probs = predict_on_image(model, undistorted, conf=0.7)
            image_with_masks = np.copy(undistorted)
            cx=0
            cy=0
            imagen_final = np.zeros((h,w),dtype=np.uint8)
            js={"shapes":[],"imagePath":"","imageWidth":w,"imageHight":h,"imageData":""}
            for i,mask_i in enumerate(masks):
                m=(255*mask_i).astype(np.uint8)
                imagen_final += m
            contours,_ = cv2.findContours(imagen_final,cv2.RETR_TREE,cv2.CHAIN_APPROX_SIMPLE)
            radios = []
            area=0
            for k,contorno in enumerate(contours):
                if contours:
                    momentos = cv2.moments(contorno)
                    area += cv2.contourArea(contorno)
                if momentos["m00"] != 0:
                    cx=int(momentos["m10"]/momentos["m00"])
                    cy=int(momentos["m01"]/momentos["m00"])
                else:
                    cx=0
                    cy=0
                holes.append([cx,cy])   
                #cv2.circle(imagen_final,(cx,cy),2,(0,0,255),-1)
                x,y = pixels2cm([cx,cy],1.125*2.5/164,1.125*2.5/166)
                x=round(x,1)
                y=round(y,1)
            radio=((area/(k+1))/(np.pi))**0.5
            ps=np.array(holes)
            xmin=np.min(ps[:,0])
            xmax=np.max(ps[:,0])
            ymin=np.min(ps[:,1])
            ymax=np.max(ps[:,1])
            puntos = sorted(holes,key=lambda punto:(punto[0]**2 + punto[1]**2)**0.5)
            #for k,[cx,cy] in enumerate(puntos):
            #    cv2.putText(imagen_final,f"{k}",(cx,cy),cv2.FONT_HERSHEY_COMPLEX,1.4,(0,255,255,1))
            #cv2.rectangle(imagen_final,(xmin,ymin),(xmax,ymax),(255,0,0),3)
            image_with_masks = overlay(image_with_masks, imagen_final, color=(20,15,200), alpha=0.4)
            #cv2.imwrite(f"dataset/{folder}/muestra_dibujadas_{nun_muestras}.jpg", undistorted)
            cv2.imwrite(f"dataset/{folder}/mascara_{nun_muestras}.jpg", imagen_final)
            nun_muestras = nun_muestras+1
            image_with_masks = cv2.resize(image_with_masks,(1200,800))
            imagen_final = cv2.resize(imagen_final,(1200,800))
            cv2.imshow("MASCARA DE HOLES EN CONOS DE BANDEJA",imagen_final)
            cv2.imshow("DETECCION EN IMAGEN",  image_with_masks)
        else:
            undistorted = cv2.resize(undistorted,(1200,800))
            cv2.imshow("DETECCION EN IMAGEN", undistorted)
        holes=[]
        if cv2.waitKey(5) & 0xFF == ord("a"):
            switch = not switch
        j=j+1
    cap.release()
    cv2.destroyAllWindows()

if __name__ == '__main__':
    main()
