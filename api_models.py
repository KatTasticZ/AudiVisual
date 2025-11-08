"""
API Routes for Custom Model Management
Endpoints for Civit.ai, HuggingFace, and custom model integration
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks, UploadFile, File
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from model_manager import ModelManager, ModelCheckpoint, POPULAR_MODELS
from generative_animator import (
    GenerativeAnimator, 
    GenerativeAnimationConfig, 
    AnimationKeyframe,
    create_deforum_animation_schedule
)
import asyncio
from pathlib import Path
import json

router = APIRouter(prefix="/api/models", tags=["models"])

# Global model manager instance
model_manager = ModelManager()
generative_animator = None

# Pydantic models for API
class CivitAIModelAdd(BaseModel):
    model_id: str = Field(..., description="Civit.ai model ID")
    version_id: Optional[str] = Field(None, description="Specific version ID (optional)")

class HuggingFaceModelAdd(BaseModel):
    repo_id: str = Field(..., description="HuggingFace repository ID")
    filename: str = Field(..., description="Model filename")
    model_type: str = Field("stable-diffusion", description="Type of model")

class CustomURLModelAdd(BaseModel):
    url: str = Field(..., description="Direct download URL")
    name: str = Field(..., description="Model name")
    model_type: str = Field(..., description="Model type")
    trigger_words: List[str] = Field(default_factory=list, description="Trigger words")
    base_model: str = Field("SD1.5", description="Base model version")

class ModelDownloadRequest(BaseModel):
    checkpoint_id: str = Field(..., description="Checkpoint ID to download")

class GenerativeAnimationRequest(BaseModel):
    # Model settings
    model_checkpoint: str = Field(..., description="Model checkpoint ID")
    lora_models: List[str] = Field(default_factory=list, description="LoRA model IDs")
    controlnet_models: List[str] = Field(default_factory=list, description="ControlNet model IDs")
    
    # Image settings
    init_image_path: str = Field(..., description="Path to initial image")
    width: int = Field(512, ge=256, le=2048)
    height: int = Field(512, ge=256, le=2048)
    
    # Animation settings
    total_frames: int = Field(120, ge=1, le=1000, description="Total frames to generate")
    fps: int = Field(24, ge=1, le=60)
    animation_mode: str = Field("3D", description="2D, 3D, or Interpolation")
    
    # Generation settings
    sampler: str = Field("DPM++ 2M Karras")
    steps: int = Field(30, ge=1, le=150)
    cfg_scale: float = Field(7.0, ge=1.0, le=30.0)
    seed: int = Field(-1, description="-1 for random")
    
    # Temporal settings
    temporal_strength: float = Field(0.5, ge=0.0, le=1.0)
    temporal_layers: int = Field(2, ge=1, le=10)
    use_animatediff: bool = Field(False)
    
    # Advanced features
    use_optical_flow: bool = Field(True)
    use_frame_interpolation: bool = Field(False)
    interpolation_factor: int = Field(2, ge=1, le=8)
    color_coherence: str = Field("Match Frame 0 LAB")
    
    # Keyframes
    keyframes: List[Dict[str, Any]] = Field(default_factory=list)
    
    # Audio reactivity
    audio_file: Optional[str] = Field(None, description="Path to audio file")

class DeforumScheduleRequest(BaseModel):
    total_frames: int = Field(..., ge=1, le=1000)
    prompt_changes: Dict[int, str] = Field(..., description="Frame number -> prompt")
    camera_movements: Dict[str, str] = Field(..., description="Parameter -> schedule string")


# ============= Model Management Endpoints =============

@router.get("/popular", response_model=Dict[str, Any])
async def get_popular_models():
    """Get list of popular pre-configured models"""
    return {
        "models": POPULAR_MODELS,
        "total": len(POPULAR_MODELS)
    }

@router.get("/library", response_model=List[Dict[str, Any]])
async def get_model_library(
    model_type: Optional[str] = None,
    downloaded_only: bool = False
):
    """
    Get user's model library
    
    - **model_type**: Filter by type (stable-diffusion, lora, controlnet, etc.)
    - **downloaded_only**: Show only downloaded models
    """
    if downloaded_only:
        models = model_manager.get_downloaded_models(model_type)
    else:
        models = model_manager.get_available_models(model_type)
    
    return [
        {
            "id": m.id,
            "name": m.name,
            "type": m.type,
            "source": m.source,
            "version": m.version,
            "base_model": m.base_model,
            "trigger_words": m.trigger_words,
            "style_tags": m.style_tags,
            "thumbnail_url": m.thumbnail_url,
            "is_downloaded": m.is_downloaded,
            "file_size": m.file_size,
            "description": m.description[:200] if m.description else "",
        }
        for m in models
    ]

@router.get("/model/{checkpoint_id}", response_model=Dict[str, Any])
async def get_model_details(checkpoint_id: str):
    """Get detailed information about a specific model"""
    model = model_manager.get_model(checkpoint_id)
    
    if not model:
        raise HTTPException(status_code=404, detail="Model not found")
    
    return {
        "id": model.id,
        "name": model.name,
        "type": model.type,
        "source": model.source,
        "path": model.path,
        "version": model.version,
        "trigger_words": model.trigger_words,
        "description": model.description,
        "style_tags": model.style_tags,
        "base_model": model.base_model,
        "recommended_settings": model.recommended_settings,
        "thumbnail_url": model.thumbnail_url,
        "download_url": model.download_url,
        "file_size": model.file_size,
        "hash": model.hash,
        "is_downloaded": model.is_downloaded,
    }

@router.post("/add/civitai", response_model=Dict[str, Any])
async def add_civitai_model(request: CivitAIModelAdd):
    """
    Add a model from Civit.ai
    
    Provide the model ID from the Civit.ai URL.
    Example: https://civitai.com/models/4201 -> model_id = "4201"
    """
    try:
        checkpoint = await model_manager.add_civitai_model(
            request.model_id,
            request.version_id
        )
        
        return {
            "success": True,
            "message": f"Added model: {checkpoint.name}",
            "checkpoint": {
                "id": checkpoint.id,
                "name": checkpoint.name,
                "type": checkpoint.type,
                "version": checkpoint.version,
                "file_size": checkpoint.file_size,
                "download_url": checkpoint.download_url,
            }
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/add/huggingface", response_model=Dict[str, Any])
async def add_huggingface_model(request: HuggingFaceModelAdd):
    """
    Add a model from HuggingFace
    
    Example:
    - repo_id: "runwayml/stable-diffusion-v1-5"
    - filename: "v1-5-pruned-emaonly.safetensors"
    """
    try:
        checkpoint = await model_manager.add_huggingface_model(
            request.repo_id,
            request.filename,
            request.model_type
        )
        
        return {
            "success": True,
            "message": f"Added model: {checkpoint.name}",
            "checkpoint": {
                "id": checkpoint.id,
                "name": checkpoint.name,
                "type": checkpoint.type,
                "download_url": checkpoint.download_url,
            }
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/add/custom", response_model=Dict[str, Any])
async def add_custom_model(request: CustomURLModelAdd):
    """
    Add a model from custom URL
    
    Direct download link to .safetensors or .ckpt file
    """
    try:
        checkpoint = await model_manager.add_custom_url_model(
            request.url,
            request.name,
            request.model_type,
            request.trigger_words,
            request.base_model
        )
        
        return {
            "success": True,
            "message": f"Added model: {checkpoint.name}",
            "checkpoint": {
                "id": checkpoint.id,
                "name": checkpoint.name,
                "type": checkpoint.type,
            }
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/download/{checkpoint_id}")
async def download_model(
    checkpoint_id: str,
    background_tasks: BackgroundTasks
):
    """
    Download a model checkpoint
    
    This runs in the background and updates progress via WebSocket
    """
    model = model_manager.get_model(checkpoint_id)
    
    if not model:
        raise HTTPException(status_code=404, detail="Model not found")
    
    if model.is_downloaded:
        return {
            "success": True,
            "message": "Model already downloaded",
            "checkpoint_id": checkpoint_id
        }
    
    # Start download in background
    async def download_task():
        try:
            await model_manager.download_model(
                checkpoint_id,
                progress_callback=lambda progress: print(f"Download progress: {progress:.1f}%")
            )
        except Exception as e:
            print(f"Download failed: {e}")
    
    background_tasks.add_task(download_task)
    
    return {
        "success": True,
        "message": f"Download started for {model.name}",
        "checkpoint_id": checkpoint_id,
        "file_size": model.file_size
    }

@router.delete("/model/{checkpoint_id}")
async def delete_model(checkpoint_id: str, remove_files: bool = True):
    """Delete a model from library"""
    model = model_manager.get_model(checkpoint_id)
    
    if not model:
        raise HTTPException(status_code=404, detail="Model not found")
    
    model_manager.delete_model(checkpoint_id, remove_files)
    
    return {
        "success": True,
        "message": f"Deleted model: {model.name}"
    }


# ============= Generative Animation Endpoints =============

@router.post("/generate/animation")
async def generate_animation(
    request: GenerativeAnimationRequest,
    background_tasks: BackgroundTasks
):
    """
    Generate a full AI animation from initial image
    
    This creates entirely new frames using Stable Diffusion, not just motion effects.
    Supports custom models, LoRAs, ControlNet, and audio-reactive generation.
    """
    global generative_animator
    
    # Validate model exists and is downloaded
    main_model = model_manager.get_model(request.model_checkpoint)
    if not main_model or not main_model.is_downloaded:
        raise HTTPException(
            status_code=400,
            detail=f"Model {request.model_checkpoint} not found or not downloaded"
        )
    
    # Validate init image exists
    init_image_path = Path(request.init_image_path)
    if not init_image_path.exists():
        raise HTTPException(status_code=400, detail="Initial image not found")
    
    # Create config
    config = GenerativeAnimationConfig(
        model_checkpoint=request.model_checkpoint,
        lora_models=request.lora_models,
        controlnet_models=request.controlnet_models,
        width=request.width,
        height=request.height,
        fps=request.fps,
        total_frames=request.total_frames,
        seed=request.seed,
        sampler=request.sampler,
        steps=request.steps,
        cfg_scale=request.cfg_scale,
        animation_mode=request.animation_mode,
        temporal_strength=request.temporal_strength,
        temporal_layers=request.temporal_layers,
        use_animatediff=request.use_animatediff,
        use_optical_flow=request.use_optical_flow,
        use_frame_interpolation=request.use_frame_interpolation,
        interpolation_factor=request.interpolation_factor,
        color_coherence=request.color_coherence,
        audio_file=request.audio_file,
        keyframes=[AnimationKeyframe(**kf) for kf in request.keyframes]
    )
    
    # Generate job ID
    import uuid
    job_id = str(uuid.uuid4())
    
    # Start generation in background
    async def generation_task():
        global generative_animator
        
        try:
            # Initialize animator
            if generative_animator is None:
                generative_animator = GenerativeAnimator(model_manager)
            
            # Load init image
            from PIL import Image
            init_image = Image.open(init_image_path).convert('RGB')
            init_image = init_image.resize((config.width, config.height))
            
            # Parse audio if provided
            audio_data = None
            if request.audio_file:
                # Load and analyze audio
                # This would integrate with the audio analyzer
                pass
            
            # Generate animation
            frames = generative_animator.generate_animation(
                init_image,
                config,
                audio_data,
                progress_callback=lambda curr, total: print(f"Frame {curr}/{total}")
            )
            
            # Save frames
            output_dir = Path(f"./outputs/{job_id}")
            output_dir.mkdir(parents=True, exist_ok=True)
            
            for i, frame in enumerate(frames):
                frame.save(output_dir / f"frame_{i:05d}.png")
            
            # Create video
            import cv2
            video_path = output_dir / "animation.mp4"
            
            first_frame = cv2.imread(str(output_dir / "frame_00000.png"))
            height, width = first_frame.shape[:2]
            
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            video = cv2.VideoWriter(str(video_path), fourcc, config.fps, (width, height))
            
            for i in range(len(frames)):
                frame_path = output_dir / f"frame_{i:05d}.png"
                frame = cv2.imread(str(frame_path))
                video.write(frame)
            
            video.release()
            
            print(f"Animation complete: {video_path}")
            
        except Exception as e:
            print(f"Generation failed: {e}")
            import traceback
            traceback.print_exc()
    
    background_tasks.add_task(generation_task)
    
    return {
        "success": True,
        "message": "Animation generation started",
        "job_id": job_id,
        "estimated_time": f"{(request.total_frames * request.steps) / 60:.1f} minutes"
    }

@router.post("/generate/deforum-schedule", response_model=List[Dict[str, Any]])
async def create_deforum_schedule(request: DeforumScheduleRequest):
    """
    Create a Deforum-style animation schedule
    
    Example:
    ```json
    {
      "total_frames": 120,
      "prompt_changes": {
        "0": "a beautiful landscape, oil painting",
        "40": "the same landscape at sunset",
        "80": "the same landscape at night with stars"
      },
      "camera_movements": {
        "zoom": "0:(1.00), 40:(1.05), 80:(1.00), 120:(1.10)",
        "angle": "0:(0), 60:(5), 120:(0)",
        "translation_x": "0:(0), 40:(10), 80:(0)",
        "rotation_3d_y": "0:(0), 120:(360)"
      }
    }
    ```
    """
    try:
        keyframes = create_deforum_animation_schedule(
            request.total_frames,
            request.prompt_changes,
            request.camera_movements
        )
        
        return [
            {
                "frame": kf.frame,
                "prompt": kf.prompt,
                "zoom": kf.zoom,
                "angle": kf.angle,
                "translation_x": kf.translation_x,
                "translation_y": kf.translation_y,
                "translation_z": kf.translation_z,
                "rotation_3d_x": kf.rotation_3d_x,
                "rotation_3d_y": kf.rotation_3d_y,
                "rotation_3d_z": kf.rotation_3d_z,
            }
            for kf in keyframes
        ]
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# ============= Search & Browse Endpoints =============

@router.get("/search/civitai")
async def search_civitai(
    query: str,
    model_type: Optional[str] = None,
    limit: int = 20
):
    """
    Search Civit.ai for models
    
    - **query**: Search term
    - **model_type**: Filter by type (Checkpoint, LORA, etc.)
    - **limit**: Number of results
    """
    import requests
    
    try:
        params = {
            "query": query,
            "limit": limit,
        }
        
        if model_type:
            params["types"] = model_type
        
        response = requests.get("https://civitai.com/api/v1/models", params=params)
        response.raise_for_status()
        data = response.json()
        
        results = []
        for model in data.get("items", []):
            latest_version = model["modelVersions"][0] if model.get("modelVersions") else {}
            
            results.append({
                "id": str(model["id"]),
                "name": model["name"],
                "type": model["type"],
                "description": model.get("description", "")[:200],
                "tags": model.get("tags", []),
                "rating": model.get("stats", {}).get("rating", 0),
                "download_count": model.get("stats", {}).get("downloadCount", 0),
                "thumbnail": latest_version.get("images", [{}])[0].get("url") if latest_version.get("images") else None,
                "base_model": latest_version.get("baseModel", "Unknown"),
            })
        
        return {
            "results": results,
            "total": len(results)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Civit.ai search failed: {str(e)}")

@router.get("/search/huggingface")
async def search_huggingface(
    query: str,
    filter_tag: str = "diffusion",
    limit: int = 20
):
    """
    Search HuggingFace for models
    
    - **query**: Search term
    - **filter_tag**: Tag filter (diffusion, lora, etc.)
    - **limit**: Number of results
    """
    try:
        from huggingface_hub import HfApi
        
        api = HfApi()
        models = api.list_models(
            search=query,
            filter=filter_tag,
            limit=limit,
            sort="downloads",
            direction=-1
        )
        
        results = []
        for model in models:
            results.append({
                "id": model.id,
                "name": model.id,
                "author": model.author if hasattr(model, 'author') else None,
                "downloads": model.downloads if hasattr(model, 'downloads') else 0,
                "likes": model.likes if hasattr(model, 'likes') else 0,
                "tags": model.tags if hasattr(model, 'tags') else [],
                "description": model.card_data.get("description", "") if model.card_data else "",
            })
        
        return {
            "results": results,
            "total": len(results)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"HuggingFace search failed: {str(e)}")
