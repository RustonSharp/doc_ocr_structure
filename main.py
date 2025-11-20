import base64
import json
from io import BytesIO

from fastapi import FastAPI, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware

from llm import LLMService
from ocr import OCREngineManager, OCREngineType
from pre_preocess import pre_preocess_for_pytesseract
from structure import structure_ocr_result

# 接口1：上传图片，进行预处理，ocr识别，llm处理，返回结果
# 返回结果包括：原始图片、预处理后的图片、最终结构化的数据
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/ocr")
async def ocr(image: UploadFile = File(...)):
    image_data = await image.read()
    pre_processed_image = pre_preocess_for_pytesseract(image_data)
    if pre_processed_image is None:
        return {"error": "预处理失败"}

    processed_bytes, processed_preview = _image_to_bytes_and_data_url(pre_processed_image)

    ocr_engine = OCREngineManager()
    input_bytes = processed_bytes if ocr_engine.current_engine == OCREngineType.PYTESSERACT else image_data
    ocr_result = await ocr_engine.process_image_with_current_engine(input_bytes)
    if ocr_result is None:
        return {"error": "ocr识别失败"}

    structured_ocr_result = structure_ocr_result(ocr_result)

    print(json.dumps(structured_ocr_result, indent=4, ensure_ascii=False))
    return {
        "pre_processed_image": processed_preview,
        "ocr_result": ocr_result,
        "structured_ocr_result": structured_ocr_result,
    }


def _image_to_bytes_and_data_url(image) -> tuple[bytes, str]:
    buffer = BytesIO()
    image.save(buffer, format="PNG")
    byte_data = buffer.getvalue()
    data_url = "data:image/png;base64," + base64.b64encode(byte_data).decode("utf-8")
    return byte_data, data_url


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
