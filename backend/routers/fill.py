"""
backend/routers/fill.py — Generative fill (inpainting)
"""
from fastapi import APIRouter, HTTPException, Header, UploadFile, File, Form
from typing import Optional
from services.generative_fill import generative_fill
from backend.utils import extract_urls

router = APIRouter(tags=["Fill"])


@router.post("/fill")
async def fill(
    file: UploadFile = File(...),
    mask: UploadFile = File(...),
    prompt: str = Form(...),
    negative_prompt: Optional[str] = Form(None),
    num_results: int = Form(1),
    sync: bool = Form(True),
    seed: Optional[int] = Form(None),
    content_moderation: bool = Form(False),
    x_api_key: str = Header(...),
):
    image_data = await file.read()
    mask_data = await mask.read()
    try:
        result = generative_fill(
            api_key=x_api_key,
            image_data=image_data,
            mask_data=mask_data,
            prompt=prompt,
            negative_prompt=negative_prompt,
            num_results=num_results,
            sync=sync,
            seed=seed,
            content_moderation=content_moderation,
        )
        urls = extract_urls(result)
        return {"result_urls": urls}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
