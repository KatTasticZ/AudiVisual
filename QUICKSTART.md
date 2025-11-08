# Quick Start Guide - 5 Minutes to Your First Video

Get the AI Animation Platform running in 5 minutes or less.

## ⚡ Prerequisites (2 minutes)

Install these if you don't have them:

```bash
# Check if installed
node --version  # Need 18+
python --version  # Need 3.9+
ffmpeg -version  # Need FFmpeg

# Install if missing:
# macOS: brew install node python ffmpeg
# Windows: Download from nodejs.org, python.org, and ffmpeg.org
# Linux: sudo apt install nodejs python3 ffmpeg
```

## 🚀 Installation (2 minutes)

```bash
# 1. Navigate to project directory
cd ai-animation-platform

# 2. Install backend dependencies
pip install fastapi uvicorn[standard] librosa moviepy opencv-python Pillow numpy

# 3. Install frontend dependencies
cd frontend
npm install
cd ..
```

## ▶️ Run the Platform (1 minute)

**Terminal 1** - Start Backend:
```bash
python main.py
```

**Terminal 2** - Start Frontend:
```bash
cd frontend
npm run dev
```

**Open Browser**: http://localhost:3000

## 🎬 Create Your First Video (2 minutes)

1. **Upload Images**: Drag 2-3 photos into the "Upload Images" area
2. **Upload Audio** (optional): Drag an MP3 file into the "Upload Audio" area
3. **Select Style**: Click "Music Video" preset
4. **Generate**: Click "Generate Animation" button
5. **Download**: Wait for processing, then click "Download Video"

**That's it! You've created your first AI-animated video.**

## 📱 Test on iPhone 16 SE

### Quick Network Setup

1. **Find your computer's IP**:
   ```bash
   # macOS/Linux
   ifconfig | grep "inet "
   
   # Windows
   ipconfig
   # Look for: 192.168.1.XXX
   ```

2. **Update frontend config** (`frontend/.env.local`):
   ```env
   NEXT_PUBLIC_API_URL=http://192.168.1.XXX:8000
   NEXT_PUBLIC_WS_URL=ws://192.168.1.XXX:8000
   ```

3. **Restart frontend**:
   ```bash
   cd frontend
   npm run dev -- -H 0.0.0.0
   ```

4. **Open on iPhone**: Safari → `http://192.168.1.XXX:3000`

5. **Add to Home Screen**: Share button → "Add to Home Screen"

## 🎨 Quick Tips

### Best Results
- Use 3-5 images for smooth transitions
- Images should be similar resolution
- Audio around 30 seconds works well
- Start with "Music Video" or "Cinematic" presets

### Faster Processing
- Use 720p resolution for testing
- Set Quality to "Fast"
- Use 24 FPS instead of 60
- Keep duration under 30 seconds

### Common Issues

**"Port already in use"**:
```bash
# Kill process on port 8000
# macOS/Linux: lsof -ti:8000 | xargs kill -9
# Windows: netstat -ano | findstr :8000, then taskkill /PID <PID> /F
```

**"Module not found"**:
```bash
pip install <module-name>
```

**Frontend won't start**:
```bash
cd frontend
rm -rf node_modules package-lock.json
npm install
```

## 📚 Next Steps

- Read [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md) for detailed setup
- Check [API_DOCUMENTATION.md](API_DOCUMENTATION.md) for API integration
- Explore different style presets
- Try advanced settings (Show Advanced button)
- Experiment with audio reactivity levels

## 🎯 Example Workflows

### Music Video from Photos
1. Upload 5-10 photos from an event
2. Add the event's soundtrack
3. Select "Music Video" preset
4. Enable "Particle Effects"
5. Set Audio Reactivity to "High"
6. Generate!

### Cinematic Slideshow
1. Upload 3-5 landscape photos
2. Select "Cinematic" preset
3. Set Zoom Effect to "In"
4. Enable "Motion Blur"
5. Use 24 FPS for film look
6. Generate!

### Psychedelic Art Video
1. Upload abstract images or artwork
2. Select "Psychedelic" preset
3. Set Motion Intensity to 90%
4. Enable all effects
5. Add electronic music
6. Generate!

## 🆘 Need Help?

- **Health Check**: Visit http://localhost:8000/health
- **API Docs**: Visit http://localhost:8000/docs
- **Check Logs**: Look at terminal output for errors
- **Test Simple First**: Try 1 image, no audio, default settings

## 🎉 You're Ready!

Start creating amazing audio-reactive animations. The platform includes:

✅ Audio-reactive effects that sync to music  
✅ Multiple artistic style presets  
✅ Real-time progress tracking  
✅ Mobile-optimized interface  
✅ Professional quality output  

**Have fun creating! 🚀✨**
