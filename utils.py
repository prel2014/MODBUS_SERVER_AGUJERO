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
