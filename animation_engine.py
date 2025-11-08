"""
Animation Engine - Core processing for audio-reactive video generation
Handles audio analysis, frame interpolation, effects, and rendering
"""

import os
import numpy as np
import cv2
from PIL import Image, ImageEnhance, ImageFilter
import asyncio
from typing import List, Dict, Tuple, Optional, AsyncGenerator
import json

# Audio processing
import librosa
import soundfile as sf

# Video processing
from moviepy.editor import ImageSequenceClip, AudioFileClip, concatenate_videoclips
from moviepy.video.fx import resize, rotate, fadein, fadeout

class AnimationEngine:
    """Main engine for processing animations"""
    
    def __init__(self, project_id: str, config):
        self.project_id = project_id
        self.config = config
        self.project_dir = os.path.join("uploads", project_id)
        self.images_dir = os.path.join(self.project_dir, "images")
        self.audio_dir = os.path.join(self.project_dir, "audio")
        self.temp_dir = os.path.join("temp", project_id)
        
        # Create temp directory
        os.makedirs(self.temp_dir, exist_ok=True)
        
        # Storage for processing
        self.images: List[np.ndarray] = []
        self.image_paths: List[str] = []
        self.audio_data: Optional[np.ndarray] = None
        self.audio_sr: int = 22050
        self.audio_features: Dict = {}
        self.frames: List[np.ndarray] = []
        
    def get_audio_file(self) -> Optional[str]:
        """Get audio file path if exists"""
        if not os.path.exists(self.audio_dir):
            return None
        
        audio_files = [f for f in os.listdir(self.audio_dir) 
                       if f.endswith(('.mp3', '.wav', '.ogg', '.m4a'))]
        
        if audio_files:
            return os.path.join(self.audio_dir, audio_files[0])
        return None
    
    async def load_images(self):
        """Load and preprocess images"""
        # Get all image files
        image_files = sorted([f for f in os.listdir(self.images_dir)
                             if f.endswith(('.jpg', '.jpeg', '.png', '.webp'))])
        
        if not image_files:
            raise ValueError("No images found in project")
        
        # Resolution mapping
        res_map = {
            "720p": (1280, 720),
            "1080p": (1920, 1080),
            "4k": (3840, 2160)
        }
        target_res = res_map.get(self.config.resolution, (1920, 1080))
        
        for img_file in image_files:
            img_path = os.path.join(self.images_dir, img_file)
            self.image_paths.append(img_path)
            
            # Load image
            img = cv2.imread(img_path)
            if img is None:
                continue
            
            # Resize to target resolution maintaining aspect ratio
            h, w = img.shape[:2]
            target_w, target_h = target_res
            
            # Calculate scaling
            scale = min(target_w / w, target_h / h)
            new_w, new_h = int(w * scale), int(h * scale)
            
            img = cv2.resize(img, (new_w, new_h), interpolation=cv2.INTER_LANCZOS4)
            
            # Pad to exact target size
            pad_w = (target_w - new_w) // 2
            pad_h = (target_h - new_h) // 2
            img = cv2.copyMakeBorder(img, pad_h, target_h - new_h - pad_h,
                                     pad_w, target_w - new_w - pad_w,
                                     cv2.BORDER_CONSTANT, value=(0, 0, 0))
            
            self.images.append(img)
        
        print(f"Loaded {len(self.images)} images at {target_res}")
    
    async def analyze_audio(self):
        """Analyze audio for beat detection and feature extraction"""
        audio_file = self.get_audio_file()
        if not audio_file:
            return
        
        # Load audio
        self.audio_data, self.audio_sr = librosa.load(audio_file, sr=22050)
        duration = len(self.audio_data) / self.audio_sr
        
        # Override duration if not set
        if self.config.duration is None:
            self.config.duration = duration
        
        # Beat tracking
        tempo, beats = librosa.beat.beat_track(y=self.audio_data, sr=self.audio_sr)
        beat_times = librosa.frames_to_time(beats, sr=self.audio_sr)
        
        # Onset detection (for sharper hits)
        onset_env = librosa.onset.onset_strength(y=self.audio_data, sr=self.audio_sr)
        onsets = librosa.onset.onset_detect(onset_envelope=onset_env, sr=self.audio_sr)
        onset_times = librosa.frames_to_time(onsets, sr=self.audio_sr)
        
        # Spectral features
        spectral_centroids = librosa.feature.spectral_centroid(y=self.audio_data, sr=self.audio_sr)[0]
        spectral_rolloff = librosa.feature.spectral_rolloff(y=self.audio_data, sr=self.audio_sr)[0]
        
        # RMS energy (loudness)
        rms = librosa.feature.rms(y=self.audio_data)[0]
        
        # Mel spectrogram for frequency analysis
        mel_spec = librosa.feature.melspectrogram(y=self.audio_data, sr=self.audio_sr, n_mels=128)
        
        # Separate frequency bands
        low_freq = np.mean(mel_spec[:32, :], axis=0)  # Bass
        mid_freq = np.mean(mel_spec[32:96, :], axis=0)  # Mids
        high_freq = np.mean(mel_spec[96:, :], axis=0)  # Highs
        
        # Store features
        self.audio_features = {
            "tempo": float(tempo),
            "duration": duration,
            "beat_times": beat_times.tolist(),
            "onset_times": onset_times.tolist(),
            "spectral_centroids": spectral_centroids,
            "spectral_rolloff": spectral_rolloff,
            "rms": rms,
            "low_freq": low_freq,
            "mid_freq": mid_freq,
            "high_freq": high_freq,
            "mel_spec": mel_spec
        }
        
        print(f"Audio analyzed: {duration:.2f}s, {tempo:.1f} BPM, {len(beat_times)} beats")
    
    async def generate_frames(self) -> AsyncGenerator[float, None]:
        """Generate interpolated frames with effects"""
        duration = self.config.duration or 10.0
        fps = self.config.fps
        total_frames = int(duration * fps)
        
        num_images = len(self.images)
        
        if num_images == 0:
            raise ValueError("No images loaded")
        
        # Determine frame distribution strategy
        if num_images == 1:
            # Single image - hold and apply effects
            base_img = self.images[0]
            for frame_idx in range(total_frames):
                frame = base_img.copy()
                self.frames.append(frame)
                
                if frame_idx % 10 == 0:
                    yield frame_idx / total_frames
        
        elif num_images >= 2:
            # Multiple images - interpolate between them
            frames_per_transition = total_frames // (num_images - 1)
            
            for img_idx in range(num_images - 1):
                img1 = self.images[img_idx]
                img2 = self.images[img_idx + 1]
                
                # Interpolate between images
                for t_idx in range(frames_per_transition):
                    alpha = t_idx / frames_per_transition
                    
                    # Apply interpolation curve
                    if self.config.interpolation == "ease-in-out":
                        alpha = self._ease_in_out(alpha)
                    elif self.config.interpolation == "bounce":
                        alpha = self._bounce(alpha)
                    
                    # Blend images
                    frame = cv2.addWeighted(img1, 1 - alpha, img2, alpha, 0)
                    self.frames.append(frame)
                    
                    if len(self.frames) % 10 == 0:
                        yield len(self.frames) / total_frames
            
            # Add final image frames to reach exact duration
            while len(self.frames) < total_frames:
                self.frames.append(self.images[-1].copy())
        
        yield 1.0
    
    async def apply_effects(self) -> AsyncGenerator[float, None]:
        """Apply motion and audio-reactive effects to frames"""
        total_frames = len(self.frames)
        
        for idx, frame in enumerate(self.frames):
            h, w = frame.shape[:2]
            
            # Apply zoom effect
            if self.config.zoom_effect != "none":
                frame = self._apply_zoom(frame, idx, total_frames)
            
            # Apply rotation
            if self.config.rotation != "none":
                frame = self._apply_rotation(frame, idx, total_frames)
            
            # Apply color grading
            if self.config.color_grading != "neutral":
                frame = self._apply_color_grading(frame)
            
            # Apply audio reactivity
            if self.config.audio_reactivity != "off" and self.audio_features:
                frame = self._apply_audio_reactive_effects(frame, idx, total_frames)
            
            # Apply motion blur
            if self.config.motion_blur and idx > 0:
                prev_frame = self.frames[idx - 1]
                frame = cv2.addWeighted(frame, 0.7, prev_frame, 0.3, 0)
            
            # Apply depth effect
            if self.config.depth_effect:
                frame = self._apply_depth_effect(frame)
            
            # Apply particle effects
            if self.config.particle_effects:
                frame = self._apply_particle_effects(frame, idx)
            
            self.frames[idx] = frame
            
            if idx % 10 == 0:
                yield idx / total_frames
        
        yield 1.0
    
    def _apply_zoom(self, frame: np.ndarray, frame_idx: int, total_frames: int) -> np.ndarray:
        """Apply zoom effect"""
        h, w = frame.shape[:2]
        progress = frame_idx / total_frames
        
        if self.config.zoom_effect == "in":
            scale = 1.0 + (progress * 0.3 * self.config.motion_intensity)
        elif self.config.zoom_effect == "out":
            scale = 1.3 - (progress * 0.3 * self.config.motion_intensity)
        elif self.config.zoom_effect == "pulse":
            scale = 1.0 + (np.sin(progress * np.pi * 4) * 0.1 * self.config.motion_intensity)
        else:
            return frame
        
        # Apply zoom
        new_w, new_h = int(w * scale), int(h * scale)
        zoomed = cv2.resize(frame, (new_w, new_h), interpolation=cv2.INTER_LANCZOS4)
        
        # Crop to original size
        start_x = (new_w - w) // 2
        start_y = (new_h - h) // 2
        
        if scale > 1.0:
            cropped = zoomed[start_y:start_y + h, start_x:start_x + w]
        else:
            cropped = np.zeros_like(frame)
            cropped[start_y:start_y + new_h, start_x:start_x + new_w] = zoomed
        
        return cropped
    
    def _apply_rotation(self, frame: np.ndarray, frame_idx: int, total_frames: int) -> np.ndarray:
        """Apply rotation effect"""
        h, w = frame.shape[:2]
        progress = frame_idx / total_frames
        
        if self.config.rotation == "cw":
            angle = progress * 360 * self.config.motion_intensity
        elif self.config.rotation == "ccw":
            angle = -progress * 360 * self.config.motion_intensity
        else:
            return frame
        
        # Rotate around center
        center = (w // 2, h // 2)
        matrix = cv2.getRotationMatrix2D(center, angle, 1.0)
        rotated = cv2.warpAffine(frame, matrix, (w, h), 
                                 flags=cv2.INTER_LANCZOS4,
                                 borderMode=cv2.BORDER_REFLECT)
        
        return rotated
    
    def _apply_color_grading(self, frame: np.ndarray) -> np.ndarray:
        """Apply color grading presets"""
        # Convert to PIL for easier color manipulation
        pil_img = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
        
        if self.config.color_grading == "warm":
            # Increase reds and yellows
            r, g, b = pil_img.split()
            r = ImageEnhance.Brightness(r).enhance(1.2)
            g = ImageEnhance.Brightness(g).enhance(1.1)
            pil_img = Image.merge("RGB", (r, g, b))
        
        elif self.config.color_grading == "cool":
            # Increase blues
            r, g, b = pil_img.split()
            b = ImageEnhance.Brightness(b).enhance(1.2)
            pil_img = Image.merge("RGB", (r, g, b))
        
        elif self.config.color_grading == "vibrant":
            # Increase saturation
            converter = ImageEnhance.Color(pil_img)
            pil_img = converter.enhance(1.5)
        
        elif self.config.color_grading == "muted":
            # Decrease saturation
            converter = ImageEnhance.Color(pil_img)
            pil_img = converter.enhance(0.6)
        
        # Convert back to numpy
        return cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)
    
    def _apply_audio_reactive_effects(self, frame: np.ndarray, frame_idx: int, total_frames: int) -> np.ndarray:
        """Apply audio-reactive effects based on beat and frequency analysis"""
        if not self.audio_features:
            return frame
        
        # Calculate current time
        duration = self.config.duration or 10.0
        current_time = (frame_idx / total_frames) * duration
        
        # Get audio frame index
        hop_length = 512
        audio_frame_idx = int((frame_idx / total_frames) * len(self.audio_features['rms']))
        audio_frame_idx = min(audio_frame_idx, len(self.audio_features['rms']) - 1)
        
        # Get intensity from RMS energy
        intensity = float(self.audio_features['rms'][audio_frame_idx])
        intensity = np.clip(intensity * 10, 0, 1)  # Normalize
        
        # Get frequency-specific intensities
        low_intensity = float(self.audio_features['low_freq'][audio_frame_idx])
        mid_intensity = float(self.audio_features['mid_freq'][audio_frame_idx])
        high_intensity = float(self.audio_features['high_freq'][audio_frame_idx])
        
        # Normalize frequency intensities
        low_intensity = np.clip(low_intensity / 100, 0, 1)
        mid_intensity = np.clip(mid_intensity / 100, 0, 1)
        high_intensity = np.clip(high_intensity / 100, 0, 1)
        
        # Select which frequency to react to
        if self.config.audio_frequency == "low":
            react_intensity = low_intensity
        elif self.config.audio_frequency == "mid":
            react_intensity = mid_intensity
        elif self.config.audio_frequency == "high":
            react_intensity = high_intensity
        else:  # "all"
            react_intensity = (low_intensity + mid_intensity + high_intensity) / 3
        
        # Apply reactivity based on settings
        reactivity_map = {"low": 0.3, "medium": 0.6, "high": 1.0}
        react_strength = reactivity_map[self.config.audio_reactivity]
        
        # Brightness pulse on beats
        brightness_boost = 1.0 + (react_intensity * react_strength * 0.3)
        frame = cv2.convertScaleAbs(frame, alpha=brightness_boost, beta=0)
        
        # Scale pulse on bass
        if self.config.audio_frequency in ["low", "all"]:
            scale_boost = 1.0 + (low_intensity * react_strength * 0.1)
            h, w = frame.shape[:2]
            new_w, new_h = int(w * scale_boost), int(h * scale_boost)
            if new_w > w:
                scaled = cv2.resize(frame, (new_w, new_h), interpolation=cv2.INTER_LINEAR)
                start_x = (new_w - w) // 2
                start_y = (new_h - h) // 2
                frame = scaled[start_y:start_y + h, start_x:start_x + w]
        
        return frame
    
    def _apply_depth_effect(self, frame: np.ndarray) -> np.ndarray:
        """Apply pseudo-3D depth effect"""
        # Simple depth via edge detection and blur
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        edges = cv2.Canny(gray, 100, 200)
        
        # Blur non-edges to simulate depth of field
        blurred = cv2.GaussianBlur(frame, (5, 5), 0)
        
        # Blend based on edges
        edges_3ch = cv2.cvtColor(edges, cv2.COLOR_GRAY2BGR) / 255.0
        result = frame * edges_3ch + blurred * (1 - edges_3ch)
        
        return result.astype(np.uint8)
    
    def _apply_particle_effects(self, frame: np.ndarray, frame_idx: int) -> np.ndarray:
        """Add particle/glitter effects"""
        h, w = frame.shape[:2]
        
        # Generate random particles
        num_particles = 50
        np.random.seed(frame_idx)  # Consistent particles per frame
        
        for _ in range(num_particles):
            x = np.random.randint(0, w)
            y = np.random.randint(0, h)
            size = np.random.randint(1, 4)
            alpha = np.random.uniform(0.3, 0.8)
            
            # Draw particle
            cv2.circle(frame, (x, y), size, (255, 255, 255), -1)
        
        return frame
    
    async def render_video(self, output_path: str) -> AsyncGenerator[float, None]:
        """Render final video with audio"""
        # Save frames to temp files
        frame_files = []
        for idx, frame in enumerate(self.frames):
            frame_path = os.path.join(self.temp_dir, f"frame_{idx:06d}.png")
            cv2.imwrite(frame_path, frame)
            frame_files.append(frame_path)
            
            if idx % 50 == 0:
                yield idx / len(self.frames) * 0.8
        
        # Create video from frames
        clip = ImageSequenceClip(frame_files, fps=self.config.fps)
        
        # Add audio if available
        audio_file = self.get_audio_file()
        if audio_file and os.path.exists(audio_file):
            audio_clip = AudioFileClip(audio_file)
            
            # Trim audio to match video duration
            if audio_clip.duration > clip.duration:
                audio_clip = audio_clip.subclip(0, clip.duration)
            
            clip = clip.set_audio(audio_clip)
        
        yield 0.9
        
        # Write video file
        clip.write_videofile(
            output_path,
            codec='libx264',
            audio_codec='aac',
            fps=self.config.fps,
            preset=self._get_ffmpeg_preset(),
            threads=4,
            logger=None  # Suppress moviepy output
        )
        
        # Cleanup
        clip.close()
        if audio_file:
            audio_clip.close()
        
        yield 1.0
    
    def _get_ffmpeg_preset(self) -> str:
        """Get FFmpeg preset based on quality setting"""
        preset_map = {
            "fast": "ultrafast",
            "balanced": "medium",
            "quality": "slow"
        }
        return preset_map.get(self.config.quality_preset, "medium")
    
    @staticmethod
    def _ease_in_out(t: float) -> float:
        """Ease-in-out interpolation curve"""
        return t * t * (3.0 - 2.0 * t)
    
    @staticmethod
    def _bounce(t: float) -> float:
        """Bounce interpolation curve"""
        return abs(np.sin(t * np.pi))
