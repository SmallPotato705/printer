from fastapi import FastAPI, UploadFile
from PIL import Image

app = FastAPI()

@app.post("/image_dimensions")
async def get_image_dimensions(image: UploadFile):
    # 檢查是否有上傳檔案
    if not image:
        return {"error": "No image uploaded."}
    
    # 檢查檔案是否為圖片格式
    if not image.filename.lower().endswith(('.jpg', '.jpeg', '.png', '.gif')):
        return {"error": "Invalid image format. Supported formats: JPG, JPEG, PNG, GIF."}
    
    # 使用 Pillow 開啟圖片
    try:
        img = Image.open(image.file)
    except Exception as e:
        return {"error": f"Failed to open image file. Error: {str(e)}"}
    
    # 取得圖片的寬度和高度
    width, height = img.size
    
    # 回傳寬度和高度
    return {"width": width, "height": height}



