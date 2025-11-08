# AI Animation Platform - API Documentation

Complete REST API reference for the AI Animation Platform.

## Base URL

```
http://localhost:8000
```

For production, replace with your deployed URL.

## API Endpoints

### 1. Health Check

Check if the API is operational.

**Endpoint**: `GET /health`

**Response**:
```json
{
  "status": "healthy",
  "timestamp": "2024-01-15T10:30:00",
  "active_projects": 2
}
```

---

### 2. Root Information

Get API information and available features.

**Endpoint**: `GET /`

**Response**:
```json
{
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
```

---

### 3. Create Project

Create a new animation project and get a unique project ID.

**Endpoint**: `POST /api/projects/create`

**Request**: No body required

**Response**:
```json
{
  "project_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "created",
  "upload_urls": {
    "images": "/api/projects/550e8400-e29b-41d4-a716-446655440000/upload/images",
    "audio": "/api/projects/550e8400-e29b-41d4-a716-446655440000/upload/audio"
  }
}
```

**Example**:
```bash
curl -X POST http://localhost:8000/api/projects/create
```

---

### 4. Upload Images

Upload one or more images to a project.

**Endpoint**: `POST /api/projects/{project_id}/upload/images`

**Request**: Multipart form data with image files

**Parameters**:
- `files`: Array of image files (JPG, PNG, WebP)

**Response**:
```json
{
  "project_id": "550e8400-e29b-41d4-a716-446655440000",
  "uploaded": 3,
  "files": [
    "image_0000.jpg",
    "image_0001.jpg",
    "image_0002.jpg"
  ]
}
```

**Example**:
```bash
curl -X POST \
  http://localhost:8000/api/projects/550e8400-e29b-41d4-a716-446655440000/upload/images \
  -F "files=@image1.jpg" \
  -F "files=@image2.jpg" \
  -F "files=@image3.jpg"
```

**Python Example**:
```python
import requests

project_id = "550e8400-e29b-41d4-a716-446655440000"
files = [
    ('files', open('image1.jpg', 'rb')),
    ('files', open('image2.jpg', 'rb')),
    ('files', open('image3.jpg', 'rb'))
]

response = requests.post(
    f'http://localhost:8000/api/projects/{project_id}/upload/images',
    files=files
)
print(response.json())
```

---

### 5. Upload Audio

Upload an audio file to a project for audio-reactive animations.

**Endpoint**: `POST /api/projects/{project_id}/upload/audio`

**Request**: Multipart form data with audio file

**Parameters**:
- `file`: Audio file (MP3, WAV, OGG, M4A)

**Response**:
```json
{
  "project_id": "550e8400-e29b-41d4-a716-446655440000",
  "audio_file": "audio.mp3",
  "status": "uploaded"
}
```

**Example**:
```bash
curl -X POST \
  http://localhost:8000/api/projects/550e8400-e29b-41d4-a716-446655440000/upload/audio \
  -F "file=@music.mp3"
```

**Python Example**:
```python
import requests

project_id = "550e8400-e29b-41d4-a716-446655440000"
files = {'file': open('music.mp3', 'rb')}

response = requests.post(
    f'http://localhost:8000/api/projects/{project_id}/upload/audio',
    files=files
)
print(response.json())
```

---

### 6. Generate Animation

Start the animation generation process with configuration.

**Endpoint**: `POST /api/projects/{project_id}/generate`

**Request Body**:
```json
{
  "project_id": "550e8400-e29b-41d4-a716-446655440000",
  "style_prompt": "cinematic, smooth motion, high quality",
  "motion_intensity": 0.7,
  "zoom_effect": "pulse",
  "rotation": "none",
  "color_grading": "vibrant",
  "fps": 30,
  "duration": 15.0,
  "interpolation": "ease-in-out",
  "audio_reactivity": "high",
  "audio_frequency": "all",
  "coherence": 0.7,
  "seed": 42,
  "resolution": "1080p",
  "quality_preset": "balanced",
  "motion_blur": false,
  "depth_effect": false,
  "particle_effects": true,
  "output_format": "mp4"
}
```

**Configuration Parameters**:

| Parameter | Type | Default | Options/Range | Description |
|-----------|------|---------|---------------|-------------|
| `style_prompt` | string | "cinematic, smooth motion, high quality" | Any text | Describes visual style |
| `motion_intensity` | float | 0.5 | 0.0 - 1.0 | Strength of motion effects |
| `zoom_effect` | string | "none" | none, in, out, pulse | Zoom animation type |
| `rotation` | string | "none" | none, cw, ccw | Rotation direction |
| `color_grading` | string | "neutral" | neutral, warm, cool, vibrant, muted | Color tone |
| `fps` | int | 30 | 24, 30, 60 | Frames per second |
| `duration` | float | null | 1.0 - 300.0 | Video length in seconds (null = audio length) |
| `interpolation` | string | "ease-in-out" | linear, ease-in-out, bounce | Frame transition curve |
| `audio_reactivity` | string | "medium" | off, low, medium, high | Audio sync strength |
| `audio_frequency` | string | "all" | low, mid, high, all | Frequency band focus |
| `coherence` | float | 0.7 | 0.0 - 1.0 | Consistency vs creativity balance |
| `seed` | int | null | Any integer | Random seed for reproducibility |
| `resolution` | string | "1080p" | 720p, 1080p, 4k | Output resolution |
| `quality_preset` | string | "balanced" | fast, balanced, quality | Encoding speed vs quality |
| `motion_blur` | bool | false | true/false | Enable motion blur effect |
| `depth_effect` | bool | false | true/false | Enable depth of field effect |
| `particle_effects` | bool | false | true/false | Enable particle overlay |
| `output_format` | string | "mp4" | mp4, webm, gif | Output file format |

**Response**:
```json
{
  "project_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "queued",
  "message": "Animation processing started"
}
```

**Example**:
```bash
curl -X POST \
  http://localhost:8000/api/projects/550e8400-e29b-41d4-a716-446655440000/generate \
  -H "Content-Type: application/json" \
  -d '{
    "project_id": "550e8400-e29b-41d4-a716-446655440000",
    "style_prompt": "music video, dynamic camera, high energy",
    "motion_intensity": 0.7,
    "audio_reactivity": "high",
    "resolution": "1080p",
    "fps": 30
  }'
```

---

### 7. Get Project Status

Check the current status and progress of a project.

**Endpoint**: `GET /api/projects/{project_id}/status`

**Response**:
```json
{
  "project_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "processing",
  "progress": 45.5,
  "message": "Generating frames...",
  "output_url": null,
  "created_at": "2024-01-15T10:30:00",
  "updated_at": "2024-01-15T10:35:00"
}
```

**Status Values**:
- `created`: Project created, awaiting uploads
- `queued`: Processing queued
- `processing`: Currently generating video
- `completed`: Video ready for download
- `failed`: Error occurred

**Example**:
```bash
curl http://localhost:8000/api/projects/550e8400-e29b-41d4-a716-446655440000/status
```

**Polling Example**:
```python
import requests
import time

project_id = "550e8400-e29b-41d4-a716-446655440000"

while True:
    response = requests.get(
        f'http://localhost:8000/api/projects/{project_id}/status'
    )
    data = response.json()
    
    print(f"Status: {data['status']} - Progress: {data['progress']}%")
    
    if data['status'] == 'completed':
        print("Video ready!")
        break
    elif data['status'] == 'failed':
        print(f"Error: {data['message']}")
        break
    
    time.sleep(2)  # Check every 2 seconds
```

---

### 8. Download Video

Download the completed video file.

**Endpoint**: `GET /api/projects/{project_id}/download`

**Response**: Binary video file (MP4)

**Example**:
```bash
curl -O http://localhost:8000/api/projects/550e8400-e29b-41d4-a716-446655440000/download
```

**Python Example**:
```python
import requests

project_id = "550e8400-e29b-41d4-a716-446655440000"

response = requests.get(
    f'http://localhost:8000/api/projects/{project_id}/download',
    stream=True
)

with open('animation.mp4', 'wb') as f:
    for chunk in response.iter_content(chunk_size=8192):
        f.write(chunk)

print("Video downloaded: animation.mp4")
```

---

### 9. Get Style Presets

Retrieve available style presets with their configurations.

**Endpoint**: `GET /api/styles/presets`

**Response**:
```json
{
  "presets": [
    {
      "name": "Cinematic",
      "prompt": "cinematic lighting, film grain, anamorphic, professional color grading",
      "settings": {
        "color_grading": "neutral",
        "motion_blur": true,
        "motion_intensity": 0.5
      }
    },
    {
      "name": "Anime",
      "prompt": "anime style, vibrant colors, cel shading, Studio Ghibli inspired",
      "settings": {
        "color_grading": "vibrant",
        "motion_intensity": 0.6
      }
    }
  ]
}
```

**Example**:
```bash
curl http://localhost:8000/api/styles/presets
```

---

### 10. Delete Project

Delete a project and all associated files.

**Endpoint**: `DELETE /api/projects/{project_id}`

**Response**:
```json
{
  "message": "Project deleted successfully"
}
```

**Example**:
```bash
curl -X DELETE http://localhost:8000/api/projects/550e8400-e29b-41d4-a716-446655440000
```

---

## WebSocket API

### Real-time Progress Updates

Connect to receive live progress updates during video generation.

**Endpoint**: `ws://localhost:8000/ws/{project_id}`

**Message Format**:
```json
{
  "project_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "processing",
  "progress": 67.3,
  "message": "Applying effects...",
  "output_url": null,
  "created_at": "2024-01-15T10:30:00",
  "updated_at": "2024-01-15T10:37:00"
}
```

**JavaScript Example**:
```javascript
const projectId = "550e8400-e29b-41d4-a716-446655440000";
const ws = new WebSocket(`ws://localhost:8000/ws/${projectId}`);

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log(`Progress: ${data.progress}%`);
  console.log(`Message: ${data.message}`);
  
  if (data.status === 'completed') {
    console.log('Video ready!');
    ws.close();
  }
};

ws.onerror = (error) => {
  console.error('WebSocket error:', error);
};
```

**Python Example**:
```python
import asyncio
import websockets
import json

async def monitor_progress(project_id):
    uri = f"ws://localhost:8000/ws/{project_id}"
    
    async with websockets.connect(uri) as websocket:
        while True:
            message = await websocket.recv()
            data = json.loads(message)
            
            print(f"Progress: {data['progress']}%")
            print(f"Message: {data['message']}")
            
            if data['status'] == 'completed':
                print("Video ready!")
                break

project_id = "550e8400-e29b-41d4-a716-446655440000"
asyncio.run(monitor_progress(project_id))
```

---

## Complete Workflow Example

### Python Script: Create Video from Images and Audio

```python
import requests
import time
import os

API_BASE = "http://localhost:8000"

# Step 1: Create project
response = requests.post(f"{API_BASE}/api/projects/create")
project = response.json()
project_id = project['project_id']
print(f"Created project: {project_id}")

# Step 2: Upload images
image_files = ['photo1.jpg', 'photo2.jpg', 'photo3.jpg']
files = [('files', open(img, 'rb')) for img in image_files]
response = requests.post(
    f"{API_BASE}/api/projects/{project_id}/upload/images",
    files=files
)
print(f"Uploaded {response.json()['uploaded']} images")

# Close file handles
for _, f in files:
    f.close()

# Step 3: Upload audio (optional)
audio_file = 'music.mp3'
if os.path.exists(audio_file):
    with open(audio_file, 'rb') as f:
        response = requests.post(
            f"{API_BASE}/api/projects/{project_id}/upload/audio",
            files={'file': f}
        )
    print(f"Uploaded audio: {response.json()['audio_file']}")

# Step 4: Configure and generate
config = {
    "project_id": project_id,
    "style_prompt": "music video, dynamic camera, vibrant colors",
    "motion_intensity": 0.8,
    "zoom_effect": "pulse",
    "color_grading": "vibrant",
    "fps": 30,
    "audio_reactivity": "high",
    "resolution": "1080p",
    "quality_preset": "balanced",
    "particle_effects": True
}

response = requests.post(
    f"{API_BASE}/api/projects/{project_id}/generate",
    json=config
)
print(f"Generation started: {response.json()['status']}")

# Step 5: Monitor progress
while True:
    response = requests.get(f"{API_BASE}/api/projects/{project_id}/status")
    status = response.json()
    
    print(f"[{status['progress']:.1f}%] {status['message']}")
    
    if status['status'] == 'completed':
        print("✅ Video generation complete!")
        break
    elif status['status'] == 'failed':
        print(f"❌ Generation failed: {status['message']}")
        exit(1)
    
    time.sleep(2)

# Step 6: Download video
response = requests.get(
    f"{API_BASE}/api/projects/{project_id}/download",
    stream=True
)

output_file = f"animation_{project_id}.mp4"
with open(output_file, 'wb') as f:
    for chunk in response.iter_content(chunk_size=8192):
        f.write(chunk)

print(f"✅ Video downloaded: {output_file}")

# Step 7: Cleanup (optional)
# requests.delete(f"{API_BASE}/api/projects/{project_id}")
```

---

## Error Handling

### HTTP Status Codes

- `200 OK`: Request successful
- `400 Bad Request`: Invalid parameters or missing files
- `404 Not Found`: Project or resource not found
- `500 Internal Server Error`: Server error during processing

### Error Response Format

```json
{
  "detail": "Error message describing what went wrong"
}
```

### Common Errors

**No images uploaded**:
```json
{
  "detail": "No images uploaded"
}
```

**Invalid file type**:
```json
{
  "detail": "Invalid file type, must be audio"
}
```

**Project not found**:
```json
{
  "detail": "Project not found"
}
```

**Video not ready**:
```json
{
  "detail": "Video not ready"
}
```

---

## Rate Limiting

Currently no rate limiting is implemented. For production:

- Recommended: 10 requests/minute per IP
- Video generation: 1 concurrent job per user
- Max project age: 24 hours before auto-deletion

---

## Best Practices

1. **Always check status** before attempting download
2. **Use WebSocket** for real-time updates instead of polling
3. **Close file handles** after uploading
4. **Handle timeouts** - video generation can take several minutes
5. **Compress images** before upload for faster processing
6. **Delete projects** after download to free server resources
7. **Use appropriate quality settings** based on use case

---

## API Limits

| Resource | Limit |
|----------|-------|
| Max images per project | 100 |
| Max image size | 50MB each |
| Max audio size | 100MB |
| Max video duration | 300 seconds (5 minutes) |
| Concurrent projects | 10 per user |

---

## Interactive API Documentation

Visit **http://localhost:8000/docs** for interactive Swagger UI documentation where you can:

- Test all endpoints directly
- View request/response schemas
- See example values
- Execute API calls from browser

---

## Support

For issues or questions:
- Check API health: `GET /health`
- View server logs for errors
- Verify file formats and sizes
- Test with minimal configuration first

---

**API Version**: 1.0.0  
**Last Updated**: 2024-01-15
