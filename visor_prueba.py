import cv2


cap = cv2.VideoCapture(4)
cap.set(3,3264)
cap.set(4,2448)
while True:
    ret,frame = cap.read()
    cv2.imshow("original",frame)
    if cv2.waitKey(10) & 0xFF == ord('q'):
        break