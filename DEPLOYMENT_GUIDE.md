# AI Animation Platform - Deployment Guide

Complete guide for deploying and testing the AI animation platform on iPhone 16 SE.

## 📋 Prerequisites

### System Requirements
- **OS**: macOS, Windows, or Linux
- **Node.js**: 18.0 or higher
- **Python**: 3.9 or higher
- **RAM**: 8GB minimum (16GB recommended)
- **Storage**: 10GB free space
- **GPU**: CUDA-compatible GPU (optional, for faster processing)

### Software Dependencies
```bash
# Check versions
node --version    # Should be 18+
npm --version     # Should be 9+
python --version  # Should be 3.9+
```

## 🚀 Installation

### Step 1: Clone or Download Project

```bash
# If using git
git clone <repository-url>
cd ai-animation-platform

# Or extract downloaded ZIP
unzip ai-animation-platform.zip
cd ai-animation-platform
```

### Step 2: Backend Setup

```bash
# Install Python dependencies
pip install -r requirements.txt

# Or use virtual environment (recommended)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

**Important**: If you encounter issues with specific packages:

```bash
# For librosa audio processing
pip install librosa soundfile

# For video processing
pip install moviepy opencv-python imageio-ffmpeg

# For AI features (optional - large downloads)
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu118
pip install diffusers transformers
```

### Step 3: Frontend Setup

```bash
# Navigate to frontend directory
cd frontend

# Install dependencies
npm install

# If you encounter peer dependency issues
npm install --legacy-peer-deps
```

### Step 4: Install FFmpeg

FFmpeg is required for video processing.

**macOS** (using Homebrew):
```bash
brew install ffmpeg
```

**Windows** (using Chocolatey):
```bash
choco install ffmpeg
```

**Linux** (Ubuntu/Debian):
```bash
sudo apt update
sudo apt install ffmpeg
```

**Verify installation**:
```bash
ffmpeg -version
```

## ⚙️ Configuration

### Environment Variables

Create `.env` file in the root directory:

```env
# Backend Configuration
API_HOST=0.0.0.0
API_PORT=8000
UPLOAD_MAX_SIZE=500MB
PROCESSING_THREADS=4

# Frontend Configuration
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_WS_URL=ws://localhost:8000

# Optional: AI Model Configuration
USE_GPU=false
MODEL_CACHE_DIR=./models
```

### Frontend Configuration

Create `frontend/.env.local`:

```env
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_WS_URL=ws://localhost:8000
```

## 🏃 Running the Platform

### Development Mode

**Terminal 1 - Backend**:
```bash
# From project root
python main.py

# Server will start at http://localhost:8000
# API docs available at http://localhost:8000/docs
```

**Terminal 2 - Frontend**:
```bash
# From frontend directory
cd frontend
npm run dev

# App will open at http://localhost:3000
```

### Production Mode

**Backend**:
```bash
# Install production server
pip install gunicorn

# Run with gunicorn
gunicorn main:app --workers 4 --worker-class uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

**Frontend**:
```bash
cd frontend
npm run build
npm start
```

## 📱 iPhone 16 SE Testing Setup

### Step 1: Network Configuration

Both devices must be on the **same Wi-Fi network**.

**Find your computer's local IP address**:

**macOS/Linux**:
```bash
ifconfig | grep "inet "
# Look for something like: 192.168.1.100
```

**Windows**:
```bash
ipconfig
# Look for IPv4 Address: 192.168.1.100
```

### Step 2: Update Configuration for Mobile Testing

Edit `frontend/.env.local`:

```env
# Replace localhost with your computer's IP
NEXT_PUBLIC_API_URL=http://192.168.1.100:8000
NEXT_PUBLIC_WS_URL=ws://192.168.1.100:8000
```

Edit `frontend/next.config.js` - update rewrites:

```javascript
async rewrites() {
  return [
    {
      source: '/api/:path*',
      destination: 'http://192.168.1.100:8000/api/:path*'  // Use your IP
    }
  ]
}
```

### Step 3: Start Servers with Network Access

**Backend**:
```bash
# Bind to all network interfaces (0.0.0.0)
python main.py
# Or explicitly:
uvicorn main:app --host 0.0.0.0 --port 8000
```

**Frontend**:
```bash
cd frontend
npm run dev -- -H 0.0.0.0
```

### Step 4: Access from iPhone

1. **Open Safari on iPhone**
2. **Navigate to**: `http://192.168.1.100:3000` (use your IP)
3. **Add to Home Screen**:
   - Tap the Share button (box with arrow)
   - Scroll down and tap "Add to Home Screen"
   - Name it "AI Animate"
   - Tap "Add"

4. **Launch the PWA**:
   - Find the icon on your home screen
   - Tap to open in fullscreen mode
   - Enjoy the native app experience!

### Step 5: Enable Developer Mode (Optional)

For debugging on iPhone:

1. **Connect iPhone to Mac** via USB
2. **On iPhone**: Settings → Safari → Advanced → Enable "Web Inspector"
3. **On Mac**: Safari → Preferences → Advanced → Show Develop menu
4. **Access Inspector**: Develop → [Your iPhone] → [Page Name]

## 🧪 Testing Workflow

### Test 1: Basic Upload
1. Open app on iPhone
2. Tap "Upload Images" area
3. Select 1-3 photos from camera roll
4. Verify images appear in preview grid

### Test 2: Audio-Reactive Animation
1. Upload 3-5 images
2. Upload an audio file (MP3)
3. Select "Music Video" preset
4. Adjust motion intensity slider
5. Tap "Generate Animation"
6. Monitor progress bar
7. Download completed video

### Test 3: Custom Configuration
1. Upload images
2. Select "Psychedelic" preset
3. Tap "Show Advanced"
4. Enable "Particle Effects"
5. Set Audio Reactivity to "High"
6. Generate and download

### Test 4: Touch Interactions
- Test pinch-to-zoom on image previews
- Swipe through uploaded images
- Drag sliders smoothly
- Test dropdown selections
- Verify all buttons are tappable

## 🐛 Troubleshooting

### Backend Issues

**Issue**: `ModuleNotFoundError: No module named 'librosa'`
```bash
pip install librosa soundfile
```

**Issue**: FFmpeg not found
```bash
# Verify installation
ffmpeg -version

# If not installed, install via package manager
# macOS: brew install ffmpeg
# Windows: choco install ffmpeg
# Linux: sudo apt install ffmpeg
```

**Issue**: Port 8000 already in use
```bash
# Kill process on port
# macOS/Linux:
lsof -ti:8000 | xargs kill -9

# Windows:
netstat -ano | findstr :8000
taskkill /PID <PID> /F
```

### Frontend Issues

**Issue**: Cannot connect to backend
- Verify backend is running: `curl http://localhost:8000/health`
- Check firewall settings
- Ensure both services are on same network

**Issue**: Styles not loading
```bash
cd frontend
npm install tailwindcss postcss autoprefixer
npx tailwindcss init -p
```

**Issue**: Build fails
```bash
# Clear cache and reinstall
rm -rf node_modules package-lock.json
npm install
npm run dev
```

### iPhone Testing Issues

**Issue**: Cannot access from iPhone
- Verify both devices on same Wi-Fi
- Check computer's firewall allows incoming connections
- Try disabling VPN on either device
- Use IP address, not localhost

**Issue**: Page loads but API calls fail
- Check CORS settings in `main.py`
- Verify API URL in `.env.local` uses correct IP
- Check network proxy settings

**Issue**: Videos not downloading
- Check browser storage permissions
- Try Safari private mode
- Clear Safari cache: Settings → Safari → Clear History

**Issue**: Upload not working
- Check file size limits (default: 500MB)
- Verify file format (JPG, PNG, MP3, WAV)
- Grant photo library permissions when prompted

## 📊 Performance Optimization

### For Faster Processing

1. **Reduce Resolution**:
   - Use 720p instead of 4K for testing
   - Lower FPS to 24 instead of 60

2. **Quality Preset**:
   - Use "Fast" preset during development
   - Switch to "Quality" for final renders

3. **Enable GPU** (if available):
   ```env
   USE_GPU=true
   ```

4. **Increase Processing Threads**:
   ```env
   PROCESSING_THREADS=8  # Match your CPU cores
   ```

### For Mobile Performance

1. **Image Optimization**:
   - Compress images before upload
   - Use JPG instead of PNG for photos
   - Max resolution: 2048x2048

2. **Network Optimization**:
   - Use 5GHz Wi-Fi band
   - Stay close to router during upload
   - Avoid concurrent downloads

3. **Browser Optimization**:
   - Close other Safari tabs
   - Clear cache regularly
   - Disable Background App Refresh

## 🔒 Security Considerations

### Development
- Backend accepts connections from any origin (CORS: *)
- No authentication required
- Suitable for local testing only

### Production Deployment
Update `main.py` CORS settings:

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://yourdomain.com"],  # Specific domain
    allow_credentials=True,
    allow_methods=["GET", "POST", "DELETE"],
    allow_headers=["*"],
)
```

Add authentication:
- Implement JWT tokens
- Add user management
- Secure file uploads
- Rate limiting

## 📈 Monitoring

### Check Backend Health
```bash
curl http://localhost:8000/health
```

### Monitor Processing
```bash
# Watch backend logs
tail -f logs/app.log

# Monitor system resources
htop  # or Activity Monitor on Mac
```

### WebSocket Testing
```bash
# Install wscat
npm install -g wscat

# Connect to WebSocket
wscat -c ws://localhost:8000/ws/PROJECT_ID
```

## 🆘 Support

### Common Questions

**Q: How long does video generation take?**
A: Depends on settings. Typically:
- 10 seconds video, 720p, Fast: ~1-2 minutes
- 30 seconds video, 1080p, Quality: ~5-10 minutes
- With AI enhancement: 2-3x longer

**Q: Can I use custom AI models?**
A: Yes, modify `animation_engine.py` to load custom Stable Diffusion models from Hugging Face or local files.

**Q: What's the maximum video length?**
A: Default: 5 minutes (300 seconds). Adjust in `main.py` AnimationConfig.

**Q: Does it work offline?**
A: Frontend has PWA caching for UI, but processing requires backend server.

### Getting Help

1. Check error messages in browser console (F12)
2. Review backend logs for detailed errors
3. Verify all dependencies are installed
4. Test with simple project (1 image, no audio)
5. Check GitHub issues for similar problems

## 🎉 Next Steps

1. ✅ Complete basic setup and testing
2. 📱 Test on iPhone 16 SE
3. 🎨 Experiment with different styles
4. 🎵 Try various audio files
5. ⚡ Optimize for your use case
6. 🚀 Deploy to production server
7. 🌟 Share your creations!

## 📝 Additional Resources

- [FFmpeg Documentation](https://ffmpeg.org/documentation.html)
- [MoviePy User Guide](https://zulko.github.io/moviepy/)
- [Librosa Audio Analysis](https://librosa.org/doc/latest/index.html)
- [Next.js Documentation](https://nextjs.org/docs)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)

---

**Happy Animating! 🎬✨**
