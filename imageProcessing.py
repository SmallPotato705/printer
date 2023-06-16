import cv2
import numpy as np

# 讀取彩色圖像
image = cv2.imread('187.jpg')

# 將圖像轉換為HSV色彩空間
hsv_image = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)

# 定義深黃色的色彩範圍，色彩、飽和、亮度
lower_yellow = np.array([20, 40, 40])
upper_yellow = np.array([200, 255, 255])

binary_image = cv2.inRange(hsv_image, lower_yellow, upper_yellow)

cv2.imshow('Original Image', image)
cv2.imshow('Binary Image', binary_image)
cv2.waitKey(0)
cv2.destroyAllWindows()
