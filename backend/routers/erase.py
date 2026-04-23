"""
backend/routers/erase.py — Erase foreground / selected object
"""
from fastapi import APIRouter, HTTPException, Header, UploadFile, File, Form
from services.erase_foreground import erase_foreground
from backend.utils import extract_urls

router = APIRouter(tags=["Erase"])


@router.post("/erase")
async def erase(
    file: UploadFile = File(...),
    content_moderation: bool = Form(False),
    x_api_key: str = Header(...),
):
    image_data = await file.read()
    try:
        result = erase_foreground(
            api_key=x_api_key,
            image_data=image_data,
            content_moderation=content_moderation,
        )
        urls = extract_urls(result)
        return {"result_urls": urls}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
