# 🚀 Updated Deployment Guide - With Generative AI Features

## 📦 New Dependencies Added

The platform now includes enterprise-level generative animation capabilities. Updated requirements:

### **Backend Requirements** (Python 3.9+)
```
# Core API
fastapi==0.104.1
uvicorn[standard]==0.24.0
python-multipart==0.0.6
websockets==12.0

# AI/ML - Generative Animation
torch>=2.0.0
diffusers>=0.25.0
transformers>=4.35.0
accelerate>=0.24.0
safetensors>=0.4.0
huggingface-hub>=0.19.0

# Image/Video Processing
Pillow>=10.0.0
opencv-python>=4.8.0
numpy>=1.24.0
scipy>=1.11.0
librosa>=0.10.0
moviepy>=1.0.3

# Utilities
pydantic>=2.0.0
requests>=2.31.0
aiofiles>=23.0.0
```

### **Frontend Dependencies** (Node.js 18+)
```json
{
  "dependencies": {
    "react": "^18.2.0",
    "next": "^14.0.0",
    "typescript": "^5.0.0",
    "tailwindcss": "^3.3.0",
    "lucide-react": "^0.294.0",
    "axios": "^1.6.0",
    "zustand": "^4.4.0",
    "framer-motion": "^10.16.0"
  }
}
```

---

## ☁️ Cloud Platform Deployment

### **Option 1: Replit (Recommended for Beginners)**

#### **Updated .replit Configuration**

Create `.replit` file:
```toml
run = "bash start.sh"
language = "python3"

[nix]
channel = "stable-23_05"

[deployment]
run = ["sh", "-c", "bash start.sh"]
deploymentTarget = "cloudrun"
```

#### **Updated replit.nix**

Create `replit.nix`:
```nix
{ pkgs }: {
  deps = [
    pkgs.python310Full
    pkgs.python310Packages.pip
    pkgs.nodejs-18_x
    pkgs.nodePackages.npm
    pkgs.ffmpeg
    pkgs.libGL
    pkgs.libGLU
    pkgs.xorg.libX11
    pkgs.xorg.libXext
    pkgs.glib
    pkgs.zlib
  ];
  
  env = {
    PYTHON_LD_LIBRARY_PATH = pkgs.lib.makeLibraryPath [
      pkgs.stdenv.cc.cc.lib
      pkgs.zlib
      pkgs.glib
    ];
    LD_LIBRARY_PATH = pkgs.lib.makeLibraryPath [
      pkgs.stdenv.cc.cc.lib
      pkgs.libGL
      pkgs.libGLU
      pkgs.xorg.libX11
      pkgs.xorg.libXext
      pkgs.glib
      pkgs.zlib
    ];
  };
}
```

#### **Updated requirements.txt for Replit**

Since Replit doesn't have GPU, we need CPU-optimized versions:

```txt
# requirements-replit.txt
fastapi==0.104.1
uvicorn[standard]==0.24.0
python-multipart==0.0.6
websockets==12.0

# AI/ML - CPU optimized
torch==2.1.0+cpu -f https://download.pytorch.org/whl/cpu/torch_stable.html
diffusers==0.25.0
transformers==4.35.0
accelerate==0.24.0
safetensors==0.4.0
huggingface-hub==0.19.0

# Image/Video Processing
Pillow==10.1.0
opencv-python-headless==4.8.1.78
numpy==1.24.3
scipy==1.11.3
librosa==0.10.1
moviepy==1.0.3

# Utilities
pydantic==2.5.0
requests==2.31.0
aiofiles==23.2.1
```

#### **Start Script for Replit**

Create `start-replit.sh`:
```bash
#!/bin/bash

echo "🚀 Starting AI Animation Platform (Replit)"

# Install backend dependencies
echo "📦 Installing Python dependencies..."
cd backend
pip install -r requirements-replit.txt --quiet

# Install frontend dependencies
echo "📦 Installing Node dependencies..."
cd ../frontend
npm install --quiet

# Build frontend
echo "🏗️ Building frontend..."
npm run build

# Start backend (with CPU-only mode)
cd ../backend
export USE_CPU=true
export PYTORCH_ENABLE_MPS_FALLBACK=1
uvicorn main:app --host 0.0.0.0 --port 8000 &

# Start frontend
cd ../frontend
npm start -- -p 3000 &

echo "✅ Platform running!"
echo "📱 Frontend: http://localhost:3000"
echo "🔌 Backend API: http://localhost:8000"
echo "📚 API Docs: http://localhost:8000/docs"

wait
```

#### **Deploying to Replit:**

1. **Create New Repl:**
   - Go to https://replit.com
   - Click "Create Repl"
   - Choose "Python" template
   - Name it "AI-Animation-Platform"

2. **Upload Files:**
   - Upload all backend files to root
   - Upload all frontend files to root
   - Upload `.replit`, `replit.nix`, `start-replit.sh`

3. **Configure Secrets:**
   - Click "Secrets" (lock icon)
   - Add: `USE_CPU=true`
   - Add: `HF_TOKEN=your_huggingface_token` (optional, for private models)

4. **Run:**
   - Click "Run" button
   - Platform will auto-install everything
   - Access via Replit URL

5. **Custom Domain (Optional):**
   - Upgrade to Replit Hacker plan
   - Link custom domain in settings

**⚠️ Replit Limitations:**
- No GPU (animations will be SLOW - 5-10 min per frame)
- 4 GB RAM limit (can't load large models)
- Better for testing UI, not production rendering

**💡 Recommendation:** Use Replit for development/testing, use RunPod/Vast.ai for actual rendering

---

### **Option 2: RunPod (Recommended for Production)**

RunPod provides GPU instances for fast rendering.

#### **Setup:**

1. **Create Account:**
   - Go to https://runpod.io
   - Sign up (get $10 free credit)

2. **Deploy Pod:**
   - Click "GPU Pods"
   - Select GPU (RTX 3090 recommended: $0.34/hr)
   - Choose "PyTorch" template
   - Deploy

3. **SSH into Pod:**
   ```bash
   ssh root@<pod-ip> -p <pod-port>
   ```

4. **Clone & Setup:**
   ```bash
   # Install system dependencies
   apt update
   apt install -y ffmpeg git nodejs npm
   
   # Upload your code or git clone
   git clone <your-repo-url>
   cd ai-animation-platform
   
   # Install backend
   cd backend
   pip install -r requirements.txt
   
   # Install frontend
   cd ../frontend
   npm install
   npm run build
   
   # Start platform
   cd ..
   bash start.sh
   ```

5. **Access:**
   - RunPod gives you public URL
   - Or use SSH tunnel: `ssh -L 3000:localhost:3000 root@<pod-ip> -p <pod-port>`

**💰 Cost Estimate:**
- RTX 3090: $0.34/hour
- 10-minute animation (~120 frames): ~$2-4
- Monthly hosting (24/7): ~$245/month
- **Pro tip:** Only run when generating, shut down when idle

---

### **Option 3: Vast.ai (Cheapest GPU Option)**

Similar to RunPod but cheaper.

#### **Setup:**

1. **Create Account:** https://vast.ai
2. **Rent GPU:**
   - Click "Search Offers"
   - Filter: RTX 3080+ (minimum), PyTorch template
   - Sort by price (as low as $0.15/hr!)
   - Click "Rent"

3. **Connect & Deploy:**
   ```bash
   # SSH to instance
   ssh -p <port> root@<host>
   
   # Same setup as RunPod
   # ... (follow RunPod steps)
   ```

**💰 Cost:** $0.15-0.30/hour for RTX 3080

---

### **Option 4: Google Colab (Free GPU for Testing)**

Free T4 GPU for 12-hour sessions.

#### **Colab Notebook:**

```python
# Install platform
!git clone <your-repo>
!cd ai-animation-platform/backend && pip install -r requirements.txt

# Start backend
import subprocess
backend = subprocess.Popen(['uvicorn', 'main:app', '--host', '0.0.0.0', '--port', '8000'], 
                          cwd='ai-animation-platform/backend')

# Expose to public URL
from google.colab import output
output.serve_kernel_port_as_window(8000)

# Or use ngrok
!pip install pyngrok
from pyngrok import ngrok
public_url = ngrok.connect(8000)
print(f"Public URL: {public_url}")
```

**Limitations:**
- 12-hour sessions (disconnects after)
- T4 GPU (slower than RTX 3090)
- Can't run 24/7
- Good for testing only

---

### **Option 5: Local Machine with GPU**

Best performance, no recurring costs.

#### **Requirements:**
- NVIDIA GPU (GTX 1660+ minimum, RTX 3060+ recommended)
- 16 GB RAM minimum (32 GB recommended)
- 50 GB free disk space (for models)
- Windows 10/11, Ubuntu 20.04+, or macOS (with MPS support)

#### **Setup:**

**Windows:**
```powershell
# Install CUDA 11.8
# Download from: https://developer.nvidia.com/cuda-11-8-0-download

# Install Python 3.10
# Download from: https://python.org

# Install Node.js 18
# Download from: https://nodejs.org

# Clone repo
git clone <your-repo>
cd ai-animation-platform

# Install backend
cd backend
pip install -r requirements.txt

# Install frontend
cd ../frontend
npm install
npm run build

# Start platform
cd ..
start.bat
```

**Linux (Ubuntu):**
```bash
# Install CUDA
sudo apt update
sudo apt install -y nvidia-cuda-toolkit

# Install dependencies
sudo apt install -y python3.10 python3-pip nodejs npm ffmpeg

# Clone & setup
git clone <your-repo>
cd ai-animation-platform

# Backend
cd backend
pip3 install -r requirements.txt

# Frontend
cd ../frontend
npm install
npm run build

# Start
cd ..
bash start.sh
```

**macOS (Apple Silicon - M1/M2/M3):**
```bash
# Install Homebrew
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Install dependencies
brew install python@3.10 node ffmpeg

# Clone & setup
git clone <your-repo>
cd ai-animation-platform

# Backend (with MPS support)
cd backend
pip3 install -r requirements.txt

# Frontend
cd ../frontend
npm install
npm run build

# Start (will auto-detect MPS)
cd ..
bash start.sh
```

---

## 🔧 Environment Configuration

Create `.env` file in root:

```env
# Platform Settings
ENVIRONMENT=production
PORT=8000
FRONTEND_PORT=3000

# GPU/CPU Settings
USE_CPU=false  # Set true for CPU-only mode
PYTORCH_CUDA_ALLOC_CONF=max_split_size_mb:512

# Model Settings
MODELS_DIR=./models
OUTPUTS_DIR=./outputs
MAX_MODEL_SIZE_GB=10

# HuggingFace (optional, for private models)
HF_TOKEN=your_token_here

# API Keys (if using external services)
CIVITAI_API_KEY=optional
OPENAI_API_KEY=optional

# Performance
MAX_WORKERS=4
BATCH_SIZE=1
ENABLE_XFORMERS=true  # Faster generation

# Security
ALLOWED_ORIGINS=http://localhost:3000,https://yourdomain.com
MAX_UPLOAD_SIZE_MB=100
```

---

## 📊 Performance Optimization

### **For Fast Generation:**

1. **Use Fast Models:**
   - SD1.5 (2 GB) - 3-5 sec/frame on RTX 3090
   - Not SDXL (7 GB) - 15-30 sec/frame

2. **Enable Optimizations:**
   ```python
   # In backend/generative_animator.py
   pipeline.enable_attention_slicing()
   pipeline.enable_xformers_memory_efficient_attention()
   pipeline.enable_vae_slicing()
   ```

3. **Lower Settings:**
   - Resolution: 512x512
   - Steps: 20
   - Diffusion cadence: 2-3

4. **Batch Processing:**
   - Generate multiple frames in parallel
   - Requires more VRAM (12+ GB)

### **For Quality:**

1. **High-Quality Models:**
   - Download "Realistic Vision V5" or "Epic Realism"
   - Use appropriate LoRAs

2. **Optimal Settings:**
   - Resolution: 1024x1024
   - Steps: 30-40
   - Sampler: DPM++ 2M Karras
   - CFG: 7-9

3. **Enable Features:**
   - Color coherence: LAB
   - Optical flow: Enabled
   - Temporal strength: 0.5-0.7

---

## 🔒 Security Best Practices

### **Production Deployment:**

1. **Enable HTTPS:**
   ```bash
   # Use Caddy (auto HTTPS)
   sudo apt install caddy
   
   # Caddyfile:
   yourdomain.com {
       reverse_proxy localhost:3000
   }
   
   api.yourdomain.com {
       reverse_proxy localhost:8000
   }
   ```

2. **Add Authentication:**
   ```python
   # In backend/main.py
   from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
   
   security = HTTPBearer()
   
   @app.post("/api/models/generate/animation")
   async def generate(credentials: HTTPAuthorizationCredentials = Depends(security)):
       # Verify token
       if credentials.credentials != "your-secret-token":
           raise HTTPException(401, "Unauthorized")
       # ... rest of code
   ```

3. **Rate Limiting:**
   ```python
   from slowapi import Limiter
   from slowapi.util import get_remote_address
   
   limiter = Limiter(key_func=get_remote_address)
   app.state.limiter = limiter
   
   @app.post("/api/models/generate/animation")
   @limiter.limit("5/hour")  # 5 generations per hour
   async def generate(request: Request):
       # ... code
   ```

4. **Firewall:**
   ```bash
   # Ubuntu UFW
   sudo ufw allow 80/tcp
   sudo ufw allow 443/tcp
   sudo ufw enable
   ```

---

## 📈 Monitoring & Logging

### **GPU Monitoring:**

```bash
# Install nvidia-smi
watch -n 1 nvidia-smi

# Or use gpustat
pip install gpustat
watch -n 1 gpustat
```

### **Application Logs:**

```python
# backend/main.py
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('app.log'),
        logging.StreamHandler()
    ]
)
```

### **Performance Metrics:**

```python
# Track generation time
import time

start = time.time()
frames = generative_animator.generate_animation(...)
end = time.time()

logger.info(f"Generated {len(frames)} frames in {end-start:.1f}s")
logger.info(f"Average: {(end-start)/len(frames):.1f}s per frame")
```

---

## 🆘 Troubleshooting

### **CUDA Out of Memory:**
```python
# Reduce batch size
config.batch_size = 1

# Enable memory optimizations
pipeline.enable_attention_slicing()
pipeline.enable_vae_slicing()

# Lower resolution
config.width = 512
config.height = 512
```

### **Slow Generation:**
```bash
# Check GPU is being used
python -c "import torch; print(torch.cuda.is_available())"

# Should print: True

# If False, reinstall PyTorch with CUDA
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu118
```

### **Model Download Fails:**
```python
# Manual download from Civit.ai
# Then place in ./models/checkpoints/

# Or use HuggingFace CLI
huggingface-cli login
huggingface-cli download runwayml/stable-diffusion-v1-5
```

---

## 🎯 Next Steps

1. **✅ Deploy to your chosen platform**
2. **✅ Download your first custom model from Civit.ai**
3. **✅ Create a test animation (30 frames)**
4. **✅ Experiment with keyframes and camera movements**
5. **✅ Try audio-reactive generation**
6. **✅ Share your creations!**

---

## 📚 Additional Resources

- **Platform Documentation:** `ADVANCED_FEATURES_GUIDE.md`
- **API Reference:** `API_DOCUMENTATION.md`
- **Quick Start:** `QUICKSTART.md`
- **Cloud Deployment:** `CLOUD_DEPLOYMENT.md`

---

**🚀 Your AI animation platform is now ready for deployment with enterprise-grade generative capabilities!**
