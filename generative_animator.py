"""
Generative Animation Engine - True AI Animation from Still Images
Supports Deforum-style, AnimateDiff, and temporal generation techniques
"""

import numpy as np
from PIL import Image
import cv2
from typing import List, Dict, Tuple, Optional, Any
import torch
from dataclasses import dataclass
from pathlib import Path
import json
import math

@dataclass
class AnimationKeyframe:
    """Keyframe for animation parameters"""
    frame: int
    prompt: str
    negative_prompt: str = ""
    strength: float = 0.75
    seed: int = -1
    zoom: float = 1.0
    angle: float = 0.0
    translation_x: float = 0.0
    translation_y: float = 0.0
    translation_z: float = 0.0
    rotation_3d_x: float = 0.0
    rotation_3d_y: float = 0.0
    rotation_3d_z: float = 0.0
    perspective_flip_theta: float = 0.0
    perspective_flip_phi: float = 0.0
    perspective_flip_gamma: float = 0.0
    noise_schedule: str = "0:(0.02)"
    color_coherence: str = "Match Frame 0 LAB"
    diffusion_cadence: int = 1
    optical_flow_cadence: str = "None"

@dataclass
class GenerativeAnimationConfig:
    """Configuration for generative animation"""
    # Model settings
    model_checkpoint: str = "stable-diffusion-v1-5"
    lora_models: List[str] = None
    controlnet_models: List[str] = None
    vae_model: Optional[str] = None
    
    # Generation settings
    width: int = 512
    height: int = 512
    fps: int = 24
    total_frames: int = 120
    seed: int = -1
    
    # Sampling settings
    sampler: str = "DPM++ 2M Karras"
    steps: int = 30
    cfg_scale: float = 7.0
    clip_skip: int = 2
    
    # Animation settings
    animation_mode: str = "3D"  # '2D', '3D', 'Video Input', 'Interpolation'
    border: str = "replicate"  # 'wrap', 'replicate'
    
    # Strength scheduling
    strength_schedule: str = "0:(0.75)"
    
    # Coherence settings
    color_coherence: str = "Match Frame 0 LAB"  # 'None', 'Match Frame 0 HSV', 'Match Frame 0 LAB', 'Match Frame 0 RGB'
    optical_flow_cadence: str = "None"  # 'None', 'RAFT', 'DIS Medium', 'DIS Fine'
    diffusion_cadence: int = 1  # Run diffusion every N frames
    
    # Temporal settings
    temporal_strength: float = 0.5  # Blend with previous frame
    temporal_layers: int = 2  # Number of previous frames to reference
    use_animatediff: bool = False
    animatediff_strength: float = 0.8
    
    # Advanced features
    use_depth_warping: bool = False
    use_optical_flow: bool = True
    use_frame_interpolation: bool = True
    interpolation_factor: int = 2
    
    # Audio reactivity
    audio_file: Optional[str] = None
    audio_reactive_params: Dict[str, str] = None  # param_name -> expression
    
    # Keyframes
    keyframes: List[AnimationKeyframe] = None
    
    def __post_init__(self):
        if self.lora_models is None:
            self.lora_models = []
        if self.controlnet_models is None:
            self.controlnet_models = []
        if self.keyframes is None:
            self.keyframes = []
        if self.audio_reactive_params is None:
            self.audio_reactive_params = {}

class GenerativeAnimator:
    """
    Advanced generative animation engine
    Generates entirely new frames using AI models, not just motion effects
    """
    
    def __init__(self, model_manager, device: str = "cuda"):
        self.model_manager = model_manager
        self.device = device
        self.pipeline = None
        self.current_config = None
        
        # Animation state
        self.previous_frames = []
        self.optical_flow_estimator = None
        self.depth_estimator = None
    
    def load_pipeline(self, config: GenerativeAnimationConfig):
        """Load Stable Diffusion pipeline with custom models"""
        try:
            from diffusers import (
                StableDiffusionPipeline, 
                StableDiffusionImg2ImgPipeline,
                ControlNetModel,
                AnimateDiffPipeline,
                DDIMScheduler,
                EulerAncestralDiscreteScheduler,
                DPMSolverMultistepScheduler
            )
        except ImportError:
            raise ImportError("Please install diffusers: pip install diffusers")
        
        # Get model checkpoint
        checkpoint = self.model_manager.get_model(config.model_checkpoint)
        if not checkpoint or not checkpoint.is_downloaded:
            raise ValueError(f"Model {config.model_checkpoint} not found or not downloaded")
        
        # Load base pipeline
        if config.use_animatediff:
            self.pipeline = AnimateDiffPipeline.from_pretrained(
                checkpoint.path,
                torch_dtype=torch.float16
            ).to(self.device)
        else:
            self.pipeline = StableDiffusionImg2ImgPipeline.from_pretrained(
                checkpoint.path,
                torch_dtype=torch.float16
            ).to(self.device)
        
        # Load LoRA models
        for lora_id in config.lora_models:
            lora = self.model_manager.get_model(lora_id)
            if lora and lora.is_downloaded:
                self.pipeline.load_lora_weights(lora.path)
        
        # Load ControlNet models
        if config.controlnet_models:
            controlnet_models = []
            for cn_id in config.controlnet_models:
                cn = self.model_manager.get_model(cn_id)
                if cn and cn.is_downloaded:
                    controlnet_models.append(
                        ControlNetModel.from_pretrained(cn.path, torch_dtype=torch.float16)
                    )
            
            if controlnet_models:
                from diffusers import StableDiffusionControlNetImg2ImgPipeline
                self.pipeline = StableDiffusionControlNetImg2ImgPipeline(
                    **self.pipeline.components,
                    controlnet=controlnet_models
                ).to(self.device)
        
        # Set sampler
        self.pipeline.scheduler = self._get_scheduler(config.sampler)
        
        # Enable optimizations
        self.pipeline.enable_attention_slicing()
        if hasattr(self.pipeline, 'enable_xformers_memory_efficient_attention'):
            try:
                self.pipeline.enable_xformers_memory_efficient_attention()
            except:
                pass
        
        self.current_config = config
    
    def generate_animation(self, init_image: Image.Image, 
                          config: GenerativeAnimationConfig,
                          audio_data: Optional[Dict] = None,
                          progress_callback: Optional[callable] = None) -> List[Image.Image]:
        """
        Generate full animation from initial image
        
        Returns list of generated frames
        """
        # Load pipeline if not loaded
        if self.pipeline is None or self.current_config != config:
            self.load_pipeline(config)
        
        frames = []
        self.previous_frames = []
        
        # Parse audio data if provided
        audio_params = self._parse_audio_data(audio_data, config.total_frames) if audio_data else {}
        
        # Generate each frame
        for frame_idx in range(config.total_frames):
            if progress_callback:
                progress_callback(frame_idx, config.total_frames)
            
            # Get keyframe data for this frame
            keyframe = self._get_keyframe_at_frame(frame_idx, config.keyframes)
            
            # Apply audio reactivity
            if audio_params:
                keyframe = self._apply_audio_reactivity(keyframe, audio_params, frame_idx)
            
            # Generate frame
            frame = self._generate_frame(
                init_image if frame_idx == 0 else frames[-1],
                frame_idx,
                keyframe,
                config
            )
            
            frames.append(frame)
            
            # Update previous frames for temporal consistency
            self.previous_frames.append(frame)
            if len(self.previous_frames) > config.temporal_layers:
                self.previous_frames.pop(0)
        
        # Post-processing: frame interpolation
        if config.use_frame_interpolation and config.interpolation_factor > 1:
            frames = self._interpolate_frames(frames, config.interpolation_factor)
        
        return frames
    
    def _generate_frame(self, prev_image: Image.Image, frame_idx: int,
                       keyframe: AnimationKeyframe, config: GenerativeAnimationConfig) -> Image.Image:
        """Generate a single frame using AI"""
        
        # Apply 2D/3D transformations to previous image
        warped_image = self._apply_transforms(
            prev_image, 
            keyframe,
            config.animation_mode,
            config.border
        )
        
        # Apply optical flow if enabled
        if config.use_optical_flow and len(self.previous_frames) > 0:
            warped_image = self._apply_optical_flow(warped_image, self.previous_frames[-1])
        
        # Prepare ControlNet inputs if using ControlNet
        controlnet_images = []
        if config.controlnet_models:
            controlnet_images = self._prepare_controlnet_inputs(warped_image, config)
        
        # Run diffusion every N frames based on cadence
        if frame_idx % config.diffusion_cadence == 0:
            # Generate new frame using Stable Diffusion
            generator = torch.Generator(device=self.device)
            if keyframe.seed > 0:
                generator.manual_seed(keyframe.seed)
            
            # Prepare prompt
            prompt = self._parse_prompt_weights(keyframe.prompt)
            
            # Generate
            if config.use_animatediff:
                # Use AnimateDiff for temporal consistency
                output = self.pipeline(
                    prompt=prompt,
                    negative_prompt=keyframe.negative_prompt,
                    image=warped_image,
                    num_frames=config.temporal_layers,
                    strength=keyframe.strength,
                    guidance_scale=config.cfg_scale,
                    num_inference_steps=config.steps,
                    generator=generator,
                ).frames[0][-1]  # Get last frame
            else:
                # Standard img2img
                output = self.pipeline(
                    prompt=prompt,
                    negative_prompt=keyframe.negative_prompt,
                    image=warped_image,
                    control_image=controlnet_images if controlnet_images else None,
                    strength=keyframe.strength,
                    guidance_scale=config.cfg_scale,
                    num_inference_steps=config.steps,
                    generator=generator,
                ).images[0]
            
            # Apply color coherence
            if config.color_coherence != "None" and len(self.previous_frames) > 0:
                reference_frame = self.previous_frames[0]  # Frame 0 or previous
                output = self._apply_color_coherence(output, reference_frame, config.color_coherence)
            
            # Blend with previous frame for temporal consistency
            if config.temporal_strength > 0 and len(self.previous_frames) > 0:
                output = self._blend_frames(output, self.previous_frames[-1], config.temporal_strength)
            
            return output
        else:
            # Skip diffusion, just use warped frame
            return warped_image
    
    def _apply_transforms(self, image: Image.Image, keyframe: AnimationKeyframe,
                         mode: str, border: str) -> Image.Image:
        """Apply 2D or 3D transformations to image"""
        
        img_array = np.array(image)
        h, w = img_array.shape[:2]
        
        if mode == "2D":
            # 2D transformations: zoom, angle, translation
            center = (w / 2, h / 2)
            
            # Create transformation matrix
            M = cv2.getRotationMatrix2D(center, keyframe.angle, keyframe.zoom)
            M[0, 2] += keyframe.translation_x
            M[1, 2] += keyframe.translation_y
            
            # Apply transformation
            if border == "wrap":
                border_mode = cv2.BORDER_WRAP
            else:
                border_mode = cv2.BORDER_REPLICATE
            
            transformed = cv2.warpAffine(img_array, M, (w, h), borderMode=border_mode)
            
        elif mode == "3D":
            # 3D transformations: full perspective control
            transformed = self._apply_3d_transform(
                img_array,
                keyframe.translation_x,
                keyframe.translation_y,
                keyframe.translation_z,
                keyframe.rotation_3d_x,
                keyframe.rotation_3d_y,
                keyframe.rotation_3d_z,
                keyframe.perspective_flip_theta,
                keyframe.perspective_flip_phi,
                keyframe.perspective_flip_gamma,
                border
            )
        else:
            transformed = img_array
        
        return Image.fromarray(transformed)
    
    def _apply_3d_transform(self, img: np.ndarray, tx: float, ty: float, tz: float,
                           rx: float, ry: float, rz: float,
                           theta: float, phi: float, gamma: float,
                           border: str) -> np.ndarray:
        """Apply 3D perspective transformation (Deforum-style)"""
        
        h, w = img.shape[:2]
        
        # Camera intrinsic matrix
        focal_length = w
        camera_matrix = np.array([
            [focal_length, 0, w / 2],
            [0, focal_length, h / 2],
            [0, 0, 1]
        ], dtype=np.float32)
        
        # Rotation matrices
        rx_rad = np.radians(rx)
        ry_rad = np.radians(ry)
        rz_rad = np.radians(rz)
        
        Rx = np.array([
            [1, 0, 0],
            [0, np.cos(rx_rad), -np.sin(rx_rad)],
            [0, np.sin(rx_rad), np.cos(rx_rad)]
        ])
        
        Ry = np.array([
            [np.cos(ry_rad), 0, np.sin(ry_rad)],
            [0, 1, 0],
            [-np.sin(ry_rad), 0, np.cos(ry_rad)]
        ])
        
        Rz = np.array([
            [np.cos(rz_rad), -np.sin(rz_rad), 0],
            [np.sin(rz_rad), np.cos(rz_rad), 0],
            [0, 0, 1]
        ])
        
        # Combined rotation
        R = Rz @ Ry @ Rx
        
        # Translation vector
        T = np.array([tx, ty, tz])
        
        # Create transformation matrix
        RT = np.hstack([R, T.reshape(3, 1)])
        projection_matrix = camera_matrix @ RT
        
        # Apply perspective transformation
        border_mode = cv2.BORDER_WRAP if border == "wrap" else cv2.BORDER_REPLICATE
        transformed = cv2.warpPerspective(img, projection_matrix[:2, :], (w, h), borderMode=border_mode)
        
        return transformed
    
    def _apply_optical_flow(self, current: Image.Image, previous: Image.Image) -> Image.Image:
        """Apply optical flow for smooth motion"""
        
        curr_array = np.array(current)
        prev_array = np.array(previous)
        
        # Convert to grayscale
        curr_gray = cv2.cvtColor(curr_array, cv2.COLOR_RGB2GRAY)
        prev_gray = cv2.cvtColor(prev_array, cv2.COLOR_RGB2GRAY)
        
        # Calculate optical flow
        flow = cv2.calcOpticalFlowFarneback(
            prev_gray, curr_gray, None,
            pyr_scale=0.5, levels=3, winsize=15,
            iterations=3, poly_n=5, poly_sigma=1.2, flags=0
        )
        
        # Create flow map
        h, w = curr_gray.shape
        flow_map = np.zeros((h, w, 2), dtype=np.float32)
        flow_map[..., 0] = np.arange(w)
        flow_map[..., 1] = np.arange(h)[:, np.newaxis]
        flow_map += flow
        
        # Remap current image using flow
        warped = cv2.remap(curr_array, flow_map, None, cv2.INTER_LINEAR)
        
        return Image.fromarray(warped)
    
    def _apply_color_coherence(self, current: Image.Image, reference: Image.Image, 
                              method: str) -> Image.Image:
        """Apply color coherence between frames"""
        
        curr_array = np.array(current).astype(np.float32)
        ref_array = np.array(reference).astype(np.float32)
        
        if method == "Match Frame 0 LAB":
            # Convert to LAB color space
            curr_lab = cv2.cvtColor(curr_array.astype(np.uint8), cv2.COLOR_RGB2LAB).astype(np.float32)
            ref_lab = cv2.cvtColor(ref_array.astype(np.uint8), cv2.COLOR_RGB2LAB).astype(np.float32)
            
            # Match mean and std of each channel
            for i in range(3):
                curr_mean, curr_std = curr_lab[..., i].mean(), curr_lab[..., i].std()
                ref_mean, ref_std = ref_lab[..., i].mean(), ref_lab[..., i].std()
                
                if curr_std > 0:
                    curr_lab[..., i] = (curr_lab[..., i] - curr_mean) * (ref_std / curr_std) + ref_mean
            
            # Convert back to RGB
            result = cv2.cvtColor(curr_lab.astype(np.uint8), cv2.COLOR_LAB2RGB)
            
        elif method == "Match Frame 0 HSV":
            # Similar process in HSV space
            curr_hsv = cv2.cvtColor(curr_array.astype(np.uint8), cv2.COLOR_RGB2HSV).astype(np.float32)
            ref_hsv = cv2.cvtColor(ref_array.astype(np.uint8), cv2.COLOR_RGB2HSV).astype(np.float32)
            
            for i in range(3):
                curr_mean, curr_std = curr_hsv[..., i].mean(), curr_hsv[..., i].std()
                ref_mean, ref_std = ref_hsv[..., i].mean(), ref_hsv[..., i].std()
                
                if curr_std > 0:
                    curr_hsv[..., i] = (curr_hsv[..., i] - curr_mean) * (ref_std / curr_std) + ref_mean
            
            result = cv2.cvtColor(curr_hsv.astype(np.uint8), cv2.COLOR_HSV2RGB)
            
        else:  # RGB
            for i in range(3):
                curr_mean, curr_std = curr_array[..., i].mean(), curr_array[..., i].std()
                ref_mean, ref_std = ref_array[..., i].mean(), ref_array[..., i].std()
                
                if curr_std > 0:
                    curr_array[..., i] = (curr_array[..., i] - curr_mean) * (ref_std / curr_std) + ref_mean
            
            result = curr_array.astype(np.uint8)
        
        return Image.fromarray(result)
    
    def _blend_frames(self, current: Image.Image, previous: Image.Image, 
                     strength: float) -> Image.Image:
        """Blend current frame with previous for temporal consistency"""
        
        curr_array = np.array(current).astype(np.float32)
        prev_array = np.array(previous).astype(np.float32)
        
        blended = curr_array * (1 - strength) + prev_array * strength
        
        return Image.fromarray(blended.astype(np.uint8))
    
    def _interpolate_frames(self, frames: List[Image.Image], factor: int) -> List[Image.Image]:
        """Interpolate between frames for higher FPS"""
        
        try:
            # Use FILM (Frame Interpolation for Large Motion) or RIFE
            # For now, simple linear interpolation
            interpolated = []
            
            for i in range(len(frames) - 1):
                interpolated.append(frames[i])
                
                curr = np.array(frames[i]).astype(np.float32)
                next_frame = np.array(frames[i + 1]).astype(np.float32)
                
                for j in range(1, factor):
                    alpha = j / factor
                    interp = curr * (1 - alpha) + next_frame * alpha
                    interpolated.append(Image.fromarray(interp.astype(np.uint8)))
            
            interpolated.append(frames[-1])
            return interpolated
            
        except Exception as e:
            print(f"Frame interpolation failed: {e}")
            return frames
    
    def _get_keyframe_at_frame(self, frame_idx: int, 
                               keyframes: List[AnimationKeyframe]) -> AnimationKeyframe:
        """Get interpolated keyframe parameters at specific frame"""
        
        if not keyframes:
            return AnimationKeyframe(frame=frame_idx, prompt="")
        
        # Find surrounding keyframes
        before = None
        after = None
        
        for kf in sorted(keyframes, key=lambda x: x.frame):
            if kf.frame <= frame_idx:
                before = kf
            if kf.frame > frame_idx and after is None:
                after = kf
        
        if before is None:
            return keyframes[0]
        if after is None:
            return before
        
        # Interpolate between keyframes
        t = (frame_idx - before.frame) / (after.frame - before.frame)
        
        return AnimationKeyframe(
            frame=frame_idx,
            prompt=before.prompt if t < 0.5 else after.prompt,
            negative_prompt=before.negative_prompt,
            strength=self._lerp(before.strength, after.strength, t),
            seed=before.seed,
            zoom=self._lerp(before.zoom, after.zoom, t),
            angle=self._lerp(before.angle, after.angle, t),
            translation_x=self._lerp(before.translation_x, after.translation_x, t),
            translation_y=self._lerp(before.translation_y, after.translation_y, t),
            translation_z=self._lerp(before.translation_z, after.translation_z, t),
            rotation_3d_x=self._lerp(before.rotation_3d_x, after.rotation_3d_x, t),
            rotation_3d_y=self._lerp(before.rotation_3d_y, after.rotation_3d_y, t),
            rotation_3d_z=self._lerp(before.rotation_3d_z, after.rotation_3d_z, t),
        )
    
    def _parse_audio_data(self, audio_data: Dict, total_frames: int) -> Dict[str, np.ndarray]:
        """Parse audio analysis data into frame-by-frame parameters"""
        
        params = {}
        
        # Resample audio features to match frame count
        for key, values in audio_data.items():
            if isinstance(values, (list, np.ndarray)):
                params[key] = np.interp(
                    np.linspace(0, len(values), total_frames),
                    np.arange(len(values)),
                    values
                )
        
        return params
    
    def _apply_audio_reactivity(self, keyframe: AnimationKeyframe, 
                                audio_params: Dict[str, np.ndarray],
                                frame_idx: int) -> AnimationKeyframe:
        """Apply audio-reactive modulation to keyframe parameters"""
        
        # Example: modulate zoom based on bass
        if 'bass' in audio_params:
            bass_value = audio_params['bass'][frame_idx]
            keyframe.zoom *= (1.0 + bass_value * 0.2)  # Up to 20% zoom
        
        # Modulate rotation based on treble
        if 'treble' in audio_params:
            treble_value = audio_params['treble'][frame_idx]
            keyframe.angle += treble_value * 45  # Up to 45 degree rotation
        
        # Modulate strength based on energy
        if 'energy' in audio_params:
            energy_value = audio_params['energy'][frame_idx]
            keyframe.strength = 0.5 + energy_value * 0.5  # 0.5 to 1.0
        
        return keyframe
    
    def _parse_prompt_weights(self, prompt: str) -> str:
        """Parse prompt with attention weights (word:weight) format"""
        # Support for (word:1.2) syntax
        # This is handled by the diffusers library automatically
        return prompt
    
    def _get_scheduler(self, sampler_name: str):
        """Get appropriate scheduler based on sampler name"""
        from diffusers import (
            DDIMScheduler,
            EulerAncestralDiscreteScheduler,
            DPMSolverMultistepScheduler,
            LMSDiscreteScheduler,
            PNDMScheduler
        )
        
        schedulers = {
            "DDIM": DDIMScheduler,
            "Euler a": EulerAncestralDiscreteScheduler,
            "DPM++ 2M Karras": lambda **kwargs: DPMSolverMultistepScheduler(**kwargs, use_karras_sigmas=True),
            "LMS": LMSDiscreteScheduler,
            "PNDM": PNDMScheduler,
        }
        
        scheduler_class = schedulers.get(sampler_name, DPMSolverMultistepScheduler)
        return scheduler_class.from_config(self.pipeline.scheduler.config)
    
    def _prepare_controlnet_inputs(self, image: Image.Image, 
                                   config: GenerativeAnimationConfig) -> List[Image.Image]:
        """Prepare ControlNet conditioning images"""
        controlnet_images = []
        
        # This would process the image based on ControlNet type
        # (e.g., extract depth, edges, pose, etc.)
        # For now, placeholder
        
        return controlnet_images
    
    @staticmethod
    def _lerp(a: float, b: float, t: float) -> float:
        """Linear interpolation"""
        return a + (b - a) * t


def create_deforum_animation_schedule(total_frames: int, 
                                      prompt_changes: Dict[int, str],
                                      camera_movements: Dict[str, str]) -> List[AnimationKeyframe]:
    """
    Create Deforum-style animation schedule
    
    Args:
        total_frames: Total number of frames
        prompt_changes: Dict of {frame_number: prompt}
        camera_movements: Dict of {parameter: schedule_string}
                         e.g., {"zoom": "0:(1.00), 30:(1.05), 60:(1.00)"}
    
    Returns:
        List of keyframes
    """
    
    keyframes = []
    
    # Parse schedules
    parsed_schedules = {}
    for param, schedule_str in camera_movements.items():
        parsed_schedules[param] = parse_schedule_string(schedule_str, total_frames)
    
    # Create keyframes for each frame with prompt change
    for frame, prompt in sorted(prompt_changes.items()):
        keyframe = AnimationKeyframe(
            frame=frame,
            prompt=prompt,
            zoom=parsed_schedules.get('zoom', [1.0] * total_frames)[frame],
            angle=parsed_schedules.get('angle', [0.0] * total_frames)[frame],
            translation_x=parsed_schedules.get('translation_x', [0.0] * total_frames)[frame],
            translation_y=parsed_schedules.get('translation_y', [0.0] * total_frames)[frame],
            translation_z=parsed_schedules.get('translation_z', [0.0] * total_frames)[frame],
            rotation_3d_x=parsed_schedules.get('rotation_3d_x', [0.0] * total_frames)[frame],
            rotation_3d_y=parsed_schedules.get('rotation_3d_y', [0.0] * total_frames)[frame],
            rotation_3d_z=parsed_schedules.get('rotation_3d_z', [0.0] * total_frames)[frame],
        )
        keyframes.append(keyframe)
    
    return keyframes


def parse_schedule_string(schedule: str, total_frames: int) -> List[float]:
    """
    Parse Deforum-style schedule string
    Format: "0:(value1), 30:(value2), 60:(value3)"
    """
    
    # Parse keyframe points
    points = []
    for part in schedule.split(','):
        part = part.strip()
        if ':' in part:
            frame_str, value_str = part.split(':')
            frame = int(frame_str.strip())
            value = float(value_str.strip('() '))
            points.append((frame, value))
    
    # Interpolate for all frames
    values = []
    for frame in range(total_frames):
        # Find surrounding points
        before = None
        after = None
        
        for f, v in points:
            if f <= frame:
                before = (f, v)
            if f > frame and after is None:
                after = (f, v)
        
        if before is None:
            values.append(points[0][1])
        elif after is None:
            values.append(before[1])
        else:
            # Linear interpolation
            t = (frame - before[0]) / (after[0] - before[0])
            value = before[1] + (after[1] - before[1]) * t
            values.append(value)
    
    return values
