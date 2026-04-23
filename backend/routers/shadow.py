"""
backend/routers/shadow.py — Add shadow to product images
"""
from fastapi import APIRouter, HTTPException, Header, UploadFile, File, Form
from typing import Optional, List
import json
from services.shadow import add_shadow
from backend.utils import extract_urls

router = APIRouter(tags=["Shadow"])


@router.post("/shadow")
async def shadow(
    file: UploadFile = File(...),
    shadow_type: str = Form("natural"),
    shadow_color: str = Form("#000000"),
    shadow_intensity: int = Form(60),
    shadow_blur: int = Form(15),
    offset_x: int = Form(0),
    offset_y: int = Form(15),
    background_color: Optional[str] = Form(None),
    force_rmbg: bool = Form(False),
    content_moderation: bool = Form(False),
    sku: Optional[str] = Form(None),
    x_api_key: str = Header(...),
):
    image_data = await file.read()
    try:
        result = add_shadow(
            api_key=x_api_key,
            image_data=image_data,
            shadow_type=shadow_type,
            shadow_color=shadow_color,
            shadow_intensity=shadow_intensity,
            shadow_blur=shadow_blur,
            shadow_offset=[offset_x, offset_y],
            background_color=background_color,
            force_rmbg=force_rmbg,
            content_moderation=content_moderation,
            sku=sku,
        )
        urls = extract_urls(result)
        return {"result_urls": urls}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
