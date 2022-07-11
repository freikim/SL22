import cv2
import numpy as np

cap = cv2.VideoCapture(0)
cv2.namedWindow('Ost')

if not cap.isOpened():
    print('Error opening camera')

while cap.isOpened():
    ret, frame = cap.read()
    if ret:
        cv2.imshow('Ost', frame)

        if cv2.waitKey(25) & 0xFF == ord('q'):
            break

    else:
        break

cap.release()

cv2.destroyAllWindows()
