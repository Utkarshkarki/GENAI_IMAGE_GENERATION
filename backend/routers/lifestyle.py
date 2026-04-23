"""
backend/routers/lifestyle.py — Lifestyle shot by text and by reference image
"""
from fastapi import APIRouter, HTTPException, Header, UploadFile, File, Form
from typing import Optional
from services.lifestyle_shot import lifestyle_shot_by_text, lifestyle_shot_by_image
from backend.utils import extract_urls

router = APIRouter(tags=["Lifestyle"])


@router.post("/lifestyle/text")
async def lifestyle_text(
    file: UploadFile = File(...),
    scene_description: str = Form(...),
    placement_type: str = Form("automatic"),
    num_results: int = Form(2),
    sync: bool = Form(True),
    fast: bool = Form(True),
    optimize_description: bool = Form(True),
    original_quality: bool = Form(False),
    shot_width: int = Form(1000),
    shot_height: int = Form(1000),
    force_rmbg: bool = Form(False),
    content_moderation: bool = Form(False),
    sku: Optional[str] = Form(None),
    x_api_key: str = Header(...),
):
    image_data = await file.read()
    try:
        result = lifestyle_shot_by_text(
            api_key=x_api_key,
            image_data=image_data,
            scene_description=scene_description,
            placement_type=placement_type,
            num_results=num_results,
            sync=sync,
            fast=fast,
            optimize_description=optimize_description,
            original_quality=original_quality,
            shot_size=[shot_width, shot_height],
            force_rmbg=force_rmbg,
            content_moderation=content_moderation,
            sku=sku,
        )
        urls = extract_urls(result)
        return {"result_urls": urls}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/lifestyle/image")
async def lifestyle_image(
    file: UploadFile = File(...),
    reference_image: UploadFile = File(...),
    placement_type: str = Form("automatic"),
    num_results: int = Form(2),
    sync: bool = Form(True),
    original_quality: bool = Form(False),
    shot_width: int = Form(1000),
    shot_height: int = Form(1000),
    force_rmbg: bool = Form(False),
    content_moderation: bool = Form(False),
    sku: Optional[str] = Form(None),
    enhance_ref_image: bool = Form(True),
    ref_image_influence: float = Form(1.0),
    x_api_key: str = Header(...),
):
    image_data = await file.read()
    ref_data = await reference_image.read()
    try:
        result = lifestyle_shot_by_image(
            api_key=x_api_key,
            image_data=image_data,
            reference_image=ref_data,
            placement_type=placement_type,
            num_results=num_results,
            sync=sync,
            original_quality=original_quality,
            shot_size=[shot_width, shot_height],
            force_rmbg=force_rmbg,
            content_moderation=content_moderation,
            sku=sku,
            enhance_ref_image=enhance_ref_image,
            ref_image_influence=ref_image_influence,
        )
        urls = extract_urls(result)
        return {"result_urls": urls}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
