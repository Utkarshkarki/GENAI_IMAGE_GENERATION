"""
backend/routers/packshot.py — Professional packshot creation
"""
from fastapi import APIRouter, HTTPException, Header, UploadFile, File, Form
from typing import Optional
from services.packshot import create_packshot
from backend.utils import extract_urls

router = APIRouter(tags=["Packshot"])


@router.post("/packshot")
async def packshot(
    file: UploadFile = File(...),
    background_color: str = Form("#FFFFFF"),
    sku: Optional[str] = Form(None),
    force_rmbg: bool = Form(False),
    content_moderation: bool = Form(False),
    x_api_key: str = Header(...),
):
    image_data = await file.read()
    try:
        result = create_packshot(
            api_key=x_api_key,
            image_data=image_data,
            background_color=background_color,
            sku=sku,
            force_rmbg=force_rmbg,
            content_moderation=content_moderation,
        )
        urls = extract_urls(result)
        return {"result_urls": urls}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
