"""
Model Manager - Custom Checkpoint Integration
Supports Civit.ai, HuggingFace, and local models for true generative animation
"""

import os
import json
import requests
import hashlib
from typing import Dict, List, Optional, Any
from pathlib import Path
from dataclasses import dataclass, asdict
import asyncio
from urllib.parse import urlparse

@dataclass
class ModelCheckpoint:
    """Represents a custom AI model checkpoint"""
    id: str
    name: str
    type: str  # 'stable-diffusion', 'controlnet', 'lora', 'animatediff', 'temporal'
    source: str  # 'civitai', 'huggingface', 'local', 'url'
    path: str
    version: str
    trigger_words: List[str]
    description: str
    style_tags: List[str]
    base_model: str  # 'SD1.5', 'SDXL', 'SD2.1', etc.
    recommended_settings: Dict[str, Any]
    thumbnail_url: Optional[str] = None
    download_url: Optional[str] = None
    file_size: Optional[int] = None
    hash: Optional[str] = None
    is_downloaded: bool = False

class ModelManager:
    """Manages custom model checkpoints from various sources"""
    
    def __init__(self, models_dir: str = "./models"):
        self.models_dir = Path(models_dir)
        self.models_dir.mkdir(parents=True, exist_ok=True)
        
        # Model subdirectories
        self.checkpoints_dir = self.models_dir / "checkpoints"
        self.loras_dir = self.models_dir / "loras"
        self.controlnet_dir = self.models_dir / "controlnet"
        self.vae_dir = self.models_dir / "vae"
        self.animatediff_dir = self.models_dir / "animatediff"
        
        for dir_path in [self.checkpoints_dir, self.loras_dir, 
                        self.controlnet_dir, self.vae_dir, self.animatediff_dir]:
            dir_path.mkdir(parents=True, exist_ok=True)
        
        self.models_db: Dict[str, ModelCheckpoint] = {}
        self.load_models_database()
    
    def load_models_database(self):
        """Load models database from JSON file"""
        db_file = self.models_dir / "models_db.json"
        if db_file.exists():
            with open(db_file, 'r') as f:
                data = json.load(f)
                self.models_db = {
                    k: ModelCheckpoint(**v) for k, v in data.items()
                }
    
    def save_models_database(self):
        """Save models database to JSON file"""
        db_file = self.models_dir / "models_db.json"
        with open(db_file, 'w') as f:
            json.dump(
                {k: asdict(v) for k, v in self.models_db.items()},
                f, indent=2
            )
    
    async def add_civitai_model(self, model_id: str, version_id: Optional[str] = None) -> ModelCheckpoint:
        """
        Add a model from Civit.ai
        
        Args:
            model_id: Civit.ai model ID
            version_id: Specific version ID (optional, uses latest if not specified)
        """
        # Fetch model info from Civit.ai API
        url = f"https://civitai.com/api/v1/models/{model_id}"
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        
        # Get the specified version or latest
        if version_id:
            version = next((v for v in data['modelVersions'] if str(v['id']) == version_id), None)
        else:
            version = data['modelVersions'][0]  # Latest version
        
        if not version:
            raise ValueError(f"Version {version_id} not found for model {model_id}")
        
        # Get primary file
        primary_file = next((f for f in version['files'] if f.get('primary', False)), version['files'][0])
        
        # Determine model type
        model_type = self._determine_model_type(data['type'])
        
        # Create checkpoint object
        checkpoint = ModelCheckpoint(
            id=f"civitai_{model_id}_{version['id']}",
            name=data['name'],
            type=model_type,
            source='civitai',
            path=str(self._get_model_dir(model_type) / primary_file['name']),
            version=version['name'],
            trigger_words=version.get('trainedWords', []),
            description=data.get('description', ''),
            style_tags=data.get('tags', []),
            base_model=version.get('baseModel', 'SD1.5'),
            recommended_settings={
                'clip_skip': version.get('clipSkip', 2),
                'steps': version.get('steps', 30),
                'cfg_scale': version.get('cfgScale', 7.0),
                'sampler': version.get('sampler', 'DPM++ 2M Karras'),
            },
            thumbnail_url=version['images'][0]['url'] if version.get('images') else None,
            download_url=primary_file['downloadUrl'],
            file_size=primary_file.get('sizeKB', 0) * 1024,
            hash=primary_file.get('hashes', {}).get('SHA256', ''),
            is_downloaded=False
        )
        
        # Add to database
        self.models_db[checkpoint.id] = checkpoint
        self.save_models_database()
        
        return checkpoint
    
    async def add_huggingface_model(self, repo_id: str, filename: str, 
                                   model_type: str = 'stable-diffusion') -> ModelCheckpoint:
        """
        Add a model from HuggingFace
        
        Args:
            repo_id: HuggingFace repo ID (e.g., 'runwayml/stable-diffusion-v1-5')
            filename: Model filename (e.g., 'v1-5-pruned-emaonly.safetensors')
            model_type: Type of model
        """
        from huggingface_hub import hf_hub_url, HfApi
        
        api = HfApi()
        
        # Get model info
        try:
            model_info = api.model_info(repo_id)
        except Exception as e:
            raise ValueError(f"Could not fetch model info from HuggingFace: {e}")
        
        # Construct download URL
        download_url = hf_hub_url(repo_id, filename)
        
        # Create checkpoint object
        checkpoint_id = f"hf_{repo_id.replace('/', '_')}_{filename.replace('.', '_')}"
        checkpoint = ModelCheckpoint(
            id=checkpoint_id,
            name=f"{repo_id}/{filename}",
            type=model_type,
            source='huggingface',
            path=str(self._get_model_dir(model_type) / filename),
            version='latest',
            trigger_words=[],
            description=model_info.card_data.get('description', '') if model_info.card_data else '',
            style_tags=model_info.tags if hasattr(model_info, 'tags') else [],
            base_model=self._infer_base_model(repo_id, filename),
            recommended_settings={
                'steps': 30,
                'cfg_scale': 7.0,
                'sampler': 'DPM++ 2M Karras',
            },
            download_url=download_url,
            is_downloaded=False
        )
        
        # Add to database
        self.models_db[checkpoint.id] = checkpoint
        self.save_models_database()
        
        return checkpoint
    
    async def add_custom_url_model(self, url: str, name: str, model_type: str,
                                   trigger_words: List[str] = None,
                                   base_model: str = 'SD1.5') -> ModelCheckpoint:
        """Add a model from a custom URL"""
        
        filename = Path(urlparse(url).path).name
        
        checkpoint = ModelCheckpoint(
            id=f"custom_{hashlib.md5(url.encode()).hexdigest()[:12]}",
            name=name,
            type=model_type,
            source='url',
            path=str(self._get_model_dir(model_type) / filename),
            version='custom',
            trigger_words=trigger_words or [],
            description=f"Custom model from {url}",
            style_tags=['custom'],
            base_model=base_model,
            recommended_settings={
                'steps': 30,
                'cfg_scale': 7.0,
            },
            download_url=url,
            is_downloaded=False
        )
        
        self.models_db[checkpoint.id] = checkpoint
        self.save_models_database()
        
        return checkpoint
    
    async def download_model(self, checkpoint_id: str, 
                           progress_callback: Optional[callable] = None) -> bool:
        """Download a model checkpoint"""
        
        if checkpoint_id not in self.models_db:
            raise ValueError(f"Model {checkpoint_id} not found in database")
        
        checkpoint = self.models_db[checkpoint_id]
        
        if checkpoint.is_downloaded:
            return True
        
        if not checkpoint.download_url:
            raise ValueError(f"No download URL available for {checkpoint_id}")
        
        # Download file
        response = requests.get(checkpoint.download_url, stream=True)
        response.raise_for_status()
        
        total_size = int(response.headers.get('content-length', 0))
        downloaded = 0
        
        output_path = Path(checkpoint.path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
                    downloaded += len(chunk)
                    
                    if progress_callback and total_size > 0:
                        progress = (downloaded / total_size) * 100
                        progress_callback(progress)
        
        # Verify hash if available
        if checkpoint.hash:
            file_hash = self._calculate_file_hash(output_path)
            if file_hash != checkpoint.hash.lower():
                output_path.unlink()
                raise ValueError(f"Hash mismatch for {checkpoint_id}")
        
        # Update status
        checkpoint.is_downloaded = True
        self.save_models_database()
        
        return True
    
    def get_available_models(self, model_type: Optional[str] = None) -> List[ModelCheckpoint]:
        """Get list of available models, optionally filtered by type"""
        models = list(self.models_db.values())
        
        if model_type:
            models = [m for m in models if m.type == model_type]
        
        return models
    
    def get_downloaded_models(self, model_type: Optional[str] = None) -> List[ModelCheckpoint]:
        """Get list of downloaded models"""
        models = [m for m in self.models_db.values() if m.is_downloaded]
        
        if model_type:
            models = [m for m in models if m.type == model_type]
        
        return models
    
    def get_model(self, checkpoint_id: str) -> Optional[ModelCheckpoint]:
        """Get a specific model checkpoint"""
        return self.models_db.get(checkpoint_id)
    
    def delete_model(self, checkpoint_id: str, remove_files: bool = True):
        """Delete a model from database and optionally remove files"""
        if checkpoint_id not in self.models_db:
            return
        
        checkpoint = self.models_db[checkpoint_id]
        
        if remove_files and checkpoint.is_downloaded:
            path = Path(checkpoint.path)
            if path.exists():
                path.unlink()
        
        del self.models_db[checkpoint_id]
        self.save_models_database()
    
    def _determine_model_type(self, civitai_type: str) -> str:
        """Convert Civit.ai model type to internal type"""
        type_map = {
            'Checkpoint': 'stable-diffusion',
            'LORA': 'lora',
            'LoCon': 'lora',
            'Hypernetwork': 'hypernetwork',
            'TextualInversion': 'embedding',
            'Controlnet': 'controlnet',
            'VAE': 'vae',
            'Poses': 'controlnet',
            'Wildcards': 'wildcards',
            'Workflows': 'workflow',
            'Other': 'other'
        }
        return type_map.get(civitai_type, 'stable-diffusion')
    
    def _get_model_dir(self, model_type: str) -> Path:
        """Get directory for model type"""
        dir_map = {
            'stable-diffusion': self.checkpoints_dir,
            'lora': self.loras_dir,
            'controlnet': self.controlnet_dir,
            'vae': self.vae_dir,
            'animatediff': self.animatediff_dir,
        }
        return dir_map.get(model_type, self.checkpoints_dir)
    
    def _infer_base_model(self, repo_id: str, filename: str) -> str:
        """Infer base model from repo ID and filename"""
        combined = (repo_id + filename).lower()
        
        if 'sdxl' in combined or 'xl' in combined:
            return 'SDXL'
        elif 'sd2' in combined or 'v2' in combined:
            return 'SD2.1'
        elif 'sd3' in combined:
            return 'SD3'
        else:
            return 'SD1.5'
    
    def _calculate_file_hash(self, filepath: Path, algorithm: str = 'sha256') -> str:
        """Calculate file hash"""
        hash_func = hashlib.new(algorithm)
        
        with open(filepath, 'rb') as f:
            for chunk in iter(lambda: f.read(8192), b''):
                hash_func.update(chunk)
        
        return hash_func.hexdigest()


# Pre-configured popular models for quick access
POPULAR_MODELS = {
    'realistic_vision': {
        'civitai_id': '4201',
        'name': 'Realistic Vision',
        'description': 'Photorealistic renders with incredible detail',
        'style': 'photorealistic'
    },
    'dreamshaper': {
        'civitai_id': '4384',
        'name': 'DreamShaper',
        'description': 'Versatile model for various art styles',
        'style': 'versatile'
    },
    'deliberate': {
        'civitai_id': '4823',
        'name': 'Deliberate',
        'description': 'High-quality artistic renders',
        'style': 'artistic'
    },
    'anime_anything': {
        'civitai_id': '9409',
        'name': 'Anything V5',
        'description': 'High-quality anime style generation',
        'style': 'anime'
    },
    'protogen': {
        'civitai_id': '3666',
        'name': 'Protogen',
        'description': 'Sci-fi and photorealistic hybrid',
        'style': 'scifi'
    },
    'absolutereality': {
        'civitai_id': '81458',
        'name': 'Absolute Reality',
        'description': 'Ultra-realistic photography style',
        'style': 'photorealistic'
    },
    'toonyou': {
        'civitai_id': '30240',
        'name': 'ToonYou',
        'description': '3D cartoon and stylized characters',
        'style': 'cartoon'
    },
    'epicrealism': {
        'civitai_id': '25694',
        'name': 'epiCRealism',
        'description': 'Cinematic photorealism',
        'style': 'cinematic'
    }
}
