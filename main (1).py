"""
AI Animation Platform - Main API Server
Audio-reactive video generation from images with AI guidance
"""

from fastapi import FastAPI, File, UploadFile, Form, BackgroundTasks, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import uvicorn
import os
import json
import asyncio
from datetime import datetime
import uuid
import shutil

# Create FastAPI app
app = FastAPI(
    title="AI Animation Platform",
    description="Audio-reactive video generation from images",
    version="1.0.0"
)

# CORS configuration for mobile/web access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create necessary directories
UPLOAD_DIR = "uploads"
OUTPUT_DIR = "outputs"
TEMP_DIR = "temp"
for directory in [UPLOAD_DIR, OUTPUT_DIR, TEMP_DIR]:
    os.makedirs(directory, exist_ok=True)

# Mount static files
app.mount("/outputs", StaticFiles(directory=OUTPUT_DIR), name="outputs")

# ============================================================================
# MODELS
# ============================================================================

class AnimationConfig(BaseModel):
    """Configuration for animation generation"""
    project_id: str
    style_prompt: str = Field(default="cinematic, smooth motion, high quality")
    motion_intensity: float = Field(default=0.5, ge=0.0, le=1.0)
    zoom_effect: str = Field(default="none")  # none, in, out, pulse
    rotation: str = Field(default="none")  # none, cw, ccw
    color_grading: str = Field(default="neutral")  # neutral, warm, cool, vibrant, muted
    fps: int = Field(default=30, ge=24, le=60)
    duration: Optional[float] = Field(default=None, ge=1.0, le=300.0)
    
    # Advanced settings
    interpolation: str = Field(default="ease-in-out")  # linear, ease-in-out, bounce
    audio_reactivity: str = Field(default="medium")  # low, medium, high, off
    audio_frequency: str = Field(default="all")  # low, mid, high, all
    coherence: float = Field(default=0.7, ge=0.0, le=1.0)
    seed: Optional[int] = Field(default=None)
    
    # Quality settings
    resolution: str = Field(default="1080p")  # 720p, 1080p, 4k
    quality_preset: str = Field(default="balanced")  # fast, balanced, quality
    
    # Effects
    motion_blur: bool = Field(default=False)
    depth_effect: bool = Field(default=False)
    particle_effects: bool = Field(default=False)
    
    # Output
    output_format: str = Field(default="mp4")  # mp4, webm, gif

class ProjectStatus(BaseModel):
    """Project processing status"""
    project_id: str
    status: str  # queued, processing, completed, failed
    progress: float = Field(default=0.0, ge=0.0, le=100.0)
    message: str = ""
    output_url: Optional[str] = None
    created_at: datetime
    updated_at: datetime

class StylePreset(BaseModel):
    """Pre-defined style preset"""
    name: str
    prompt: str
    settings: Dict[str, Any]

# ============================================================================
# GLOBAL STATE
# ============================================================================

# Store active projects and their status
projects: Dict[str, ProjectStatus] = {}

# WebSocket connections for real-time updates
active_connections: Dict[str, WebSocket] = {}

# Style presets (inspired by Midjourney)
STYLE_PRESETS = [
    {
        "name": "Cinematic",
        "prompt": "cinematic lighting, film grain, anamorphic, professional color grading",
        "settings": {"color_grading": "neutral", "motion_blur": True}
    },
    {
        "name": "Anime",
        "prompt": "anime style, vibrant colors, cel shading, Studio Ghibli inspired",
        "settings": {"color_grading": "vibrant", "motion_intensity": 0.6}
    },
    {
        "name": "Cyberpunk",
        "prompt": "cyberpunk, neon lights, dystopian, futuristic, blade runner aesthetic",
        "settings": {"color_grading": "cool", "particle_effects": True}
    },
    {
        "name": "Vintage",
        "prompt": "vintage film, retro, nostalgic, 8mm film aesthetic, warm tones",
        "settings": {"color_grading": "warm", "motion_blur": True}
    },
    {
        "name": "Abstract",
        "prompt": "abstract art, surreal, dreamlike, flowing patterns",
        "settings": {"motion_intensity": 0.8, "particle_effects": True}
    },
    {
        "name": "Music Video",
        "prompt": "music video, dynamic camera, high energy, professional production",
        "settings": {"audio_reactivity": "high", "motion_intensity": 0.7}
    },
    {
        "name": "Documentary",
        "prompt": "documentary style, natural lighting, realistic, subtle motion",
        "settings": {"motion_intensity": 0.3, "audio_reactivity": "low"}
    },
    {
        "name": "Psychedelic",
        "prompt": "psychedelic, trippy, kaleidoscopic, vibrant colors, fluid motion",
        "settings": {"motion_intensity": 0.9, "particle_effects": True, "color_grading": "vibrant"}
    }
]

# ============================================================================
# API ENDPOINTS
# ============================================================================

@app.get("/")
async def root():
    """API status and information"""
    return {
        "name": "AI Animation Platform",
        "version": "1.0.0",
        "status": "operational",
        "features": [
            "Audio-reactive animation",
            "Image-to-video transformation",
            "Text-guided generation",
            "Real-time preview",
            "Mobile optimized"
        ]
    }

@app.post("/api/projects/create")
async def create_project():
    """Create a new animation project"""
    project_id = str(uuid.uuid4())
    
    # Create project directory
    project_dir = os.path.join(UPLOAD_DIR, project_id)
    os.makedirs(project_dir, exist_ok=True)
    os.makedirs(os.path.join(project_dir, "images"), exist_ok=True)
    os.makedirs(os.path.join(project_dir, "audio"), exist_ok=True)
    
    # Initialize project status
    projects[project_id] = ProjectStatus(
        project_id=project_id,
        status="created",
        progress=0.0,
        message="Project created, awaiting uploads",
        created_at=datetime.now(),
        updated_at=datetime.now()
    )
    
    return {
        "project_id": project_id,
        "status": "created",
        "upload_urls": {
            "images": f"/api/projects/{project_id}/upload/images",
            "audio": f"/api/projects/{project_id}/upload/audio"
        }
    }

@app.post("/api/projects/{project_id}/upload/images")
async def upload_images(project_id: str, files: List[UploadFile] = File(...)):
    """Upload images for animation"""
    if project_id not in projects:
        raise HTTPException(status_code=404, detail="Project not found")
    
    project_dir = os.path.join(UPLOAD_DIR, project_id, "images")
    uploaded_files = []
    
    for idx, file in enumerate(files):
        if not file.content_type.startswith("image/"):
            continue
        
        # Save file with sequential naming
        ext = os.path.splitext(file.filename)[1]
        filename = f"image_{idx:04d}{ext}"
        filepath = os.path.join(project_dir, filename)
        
        with open(filepath, "wb") as f:
            content = await file.read()
            f.write(content)
        
        uploaded_files.append(filename)
    
    # Update project status
    projects[project_id].message = f"Uploaded {len(uploaded_files)} images"
    projects[project_id].updated_at = datetime.now()
    
    return {
        "project_id": project_id,
        "uploaded": len(uploaded_files),
        "files": uploaded_files
    }

@app.post("/api/projects/{project_id}/upload/audio")
async def upload_audio(project_id: str, file: UploadFile = File(...)):
    """Upload audio file for synchronization"""
    if project_id not in projects:
        raise HTTPException(status_code=404, detail="Project not found")
    
    if not file.content_type.startswith("audio/"):
        raise HTTPException(status_code=400, detail="Invalid file type, must be audio")
    
    # Save audio file
    project_dir = os.path.join(UPLOAD_DIR, project_id, "audio")
    ext = os.path.splitext(file.filename)[1]
    filename = f"audio{ext}"
    filepath = os.path.join(project_dir, filename)
    
    with open(filepath, "wb") as f:
        content = await file.read()
        f.write(content)
    
    # Update project status
    projects[project_id].message = "Audio file uploaded"
    projects[project_id].updated_at = datetime.now()
    
    return {
        "project_id": project_id,
        "audio_file": filename,
        "status": "uploaded"
    }

@app.post("/api/projects/{project_id}/generate")
async def generate_animation(
    project_id: str,
    config: AnimationConfig,
    background_tasks: BackgroundTasks
):
    """Generate animation with given configuration"""
    if project_id not in projects:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # Validate project has required files
    project_dir = os.path.join(UPLOAD_DIR, project_id)
    images_dir = os.path.join(project_dir, "images")
    
    if not os.path.exists(images_dir) or not os.listdir(images_dir):
        raise HTTPException(status_code=400, detail="No images uploaded")
    
    # Update status
    projects[project_id].status = "queued"
    projects[project_id].message = "Animation queued for processing"
    projects[project_id].updated_at = datetime.now()
    
    # Add processing task to background
    background_tasks.add_task(process_animation, project_id, config)
    
    return {
        "project_id": project_id,
        "status": "queued",
        "message": "Animation processing started"
    }

@app.get("/api/projects/{project_id}/status")
async def get_project_status(project_id: str):
    """Get current project status"""
    if project_id not in projects:
        raise HTTPException(status_code=404, detail="Project not found")
    
    return projects[project_id]

@app.get("/api/projects/{project_id}/download")
async def download_video(project_id: str):
    """Download completed video"""
    if project_id not in projects:
        raise HTTPException(status_code=404, detail="Project not found")
    
    if projects[project_id].status != "completed":
        raise HTTPException(status_code=400, detail="Video not ready")
    
    output_file = os.path.join(OUTPUT_DIR, f"{project_id}.mp4")
    
    if not os.path.exists(output_file):
        raise HTTPException(status_code=404, detail="Output file not found")
    
    return FileResponse(
        output_file,
        media_type="video/mp4",
        filename=f"animation_{project_id}.mp4"
    )

@app.get("/api/styles/presets")
async def get_style_presets():
    """Get available style presets"""
    return {"presets": STYLE_PRESETS}

@app.delete("/api/projects/{project_id}")
async def delete_project(project_id: str):
    """Delete project and associated files"""
    if project_id not in projects:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # Delete project directory
    project_dir = os.path.join(UPLOAD_DIR, project_id)
    if os.path.exists(project_dir):
        shutil.rmtree(project_dir)
    
    # Delete output file
    output_file = os.path.join(OUTPUT_DIR, f"{project_id}.mp4")
    if os.path.exists(output_file):
        os.remove(output_file)
    
    # Remove from tracking
    del projects[project_id]
    
    return {"message": "Project deleted successfully"}

# ============================================================================
# WEBSOCKET FOR REAL-TIME UPDATES
# ============================================================================

@app.websocket("/ws/{project_id}")
async def websocket_endpoint(websocket: WebSocket, project_id: str):
    """WebSocket connection for real-time progress updates"""
    await websocket.accept()
    active_connections[project_id] = websocket
    
    try:
        while True:
            # Send current status every second
            if project_id in projects:
                await websocket.send_json(projects[project_id].dict())
            await asyncio.sleep(1)
            
    except WebSocketDisconnect:
        if project_id in active_connections:
            del active_connections[project_id]

async def notify_project_update(project_id: str):
    """Send update to connected WebSocket client"""
    if project_id in active_connections:
        try:
            await active_connections[project_id].send_json(
                projects[project_id].dict()
            )
        except:
            pass

# ============================================================================
# BACKGROUND PROCESSING
# ============================================================================

async def process_animation(project_id: str, config: AnimationConfig):
    """
    Background task to process animation
    This is where the main AI animation logic happens
    """
    try:
        # Update status
        projects[project_id].status = "processing"
        projects[project_id].progress = 0.0
        projects[project_id].message = "Initializing..."
        projects[project_id].updated_at = datetime.now()
        await notify_project_update(project_id)
        
        # Import processing modules
        from animation_engine import AnimationEngine
        
        # Initialize engine
        engine = AnimationEngine(project_id, config)
        
        # Step 1: Load and preprocess images (10%)
        projects[project_id].message = "Loading images..."
        projects[project_id].progress = 5.0
        await notify_project_update(project_id)
        
        await engine.load_images()
        projects[project_id].progress = 10.0
        await notify_project_update(project_id)
        
        # Step 2: Analyze audio if present (20%)
        audio_file = engine.get_audio_file()
        if audio_file and config.audio_reactivity != "off":
            projects[project_id].message = "Analyzing audio..."
            projects[project_id].progress = 15.0
            await notify_project_update(project_id)
            
            await engine.analyze_audio()
            projects[project_id].progress = 20.0
            await notify_project_update(project_id)
        else:
            projects[project_id].progress = 20.0
        
        # Step 3: Generate interpolated frames (30-70%)
        projects[project_id].message = "Generating frames..."
        
        async for progress in engine.generate_frames():
            projects[project_id].progress = 20.0 + (progress * 0.5)
            await notify_project_update(project_id)
        
        projects[project_id].progress = 70.0
        await notify_project_update(project_id)
        
        # Step 4: Apply effects (70-85%)
        projects[project_id].message = "Applying effects..."
        
        async for progress in engine.apply_effects():
            projects[project_id].progress = 70.0 + (progress * 0.15)
            await notify_project_update(project_id)
        
        projects[project_id].progress = 85.0
        await notify_project_update(project_id)
        
        # Step 5: Render video (85-100%)
        projects[project_id].message = "Rendering video..."
        
        output_path = os.path.join(OUTPUT_DIR, f"{project_id}.mp4")
        
        async for progress in engine.render_video(output_path):
            projects[project_id].progress = 85.0 + (progress * 0.15)
            await notify_project_update(project_id)
        
        # Complete
        projects[project_id].status = "completed"
        projects[project_id].progress = 100.0
        projects[project_id].message = "Video generated successfully"
        projects[project_id].output_url = f"/api/projects/{project_id}/download"
        projects[project_id].updated_at = datetime.now()
        await notify_project_update(project_id)
        
    except Exception as e:
        # Handle errors
        projects[project_id].status = "failed"
        projects[project_id].message = f"Error: {str(e)}"
        projects[project_id].updated_at = datetime.now()
        await notify_project_update(project_id)
        print(f"Error processing project {project_id}: {e}")

# ============================================================================
# HEALTH CHECK
# ============================================================================

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "active_projects": len([p for p in projects.values() if p.status == "processing"])
    }

# ============================================================================
# MAIN
# ============================================================================

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
