/**
 * Model Marketplace Component
 * Browse and download models from Civit.ai, HuggingFace, and custom sources
 */

import React, { useState, useEffect } from 'react';
import { Search, Download, Check, Trash2, ExternalLink, Star, TrendingUp } from 'lucide-react';

interface Model {
  id: string;
  name: string;
  type: string;
  source: string;
  description: string;
  thumbnail_url?: string;
  is_downloaded: boolean;
  file_size?: number;
  rating?: number;
  download_count?: number;
  tags?: string[];
  base_model?: string;
  trigger_words?: string[];
}

interface ModelMarketplaceProps {
  onModelSelect?: (modelId: string) => void;
}

export default function ModelMarketplace({ onModelSelect }: ModelMarketplaceProps) {
  const [activeTab, setActiveTab] = useState<'library' | 'civitai' | 'huggingface' | 'custom'>('library');
  const [searchQuery, setSearchQuery] = useState('');
  const [models, setModels] = useState<Model[]>([]);
  const [loading, setLoading] = useState(false);
  const [selectedModel, setSelectedModel] = useState<Model | null>(null);
  const [filterType, setFilterType] = useState<string>('all');
  
  // Custom model form
  const [customUrl, setCustomUrl] = useState('');
  const [customName, setCustomName] = useState('');
  const [customType, setCustomType] = useState('stable-diffusion');
  
  // Load library on mount
  useEffect(() => {
    if (activeTab === 'library') {
      loadLibrary();
    }
  }, [activeTab, filterType]);
  
  const loadLibrary = async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams();
      if (filterType !== 'all') params.append('model_type', filterType);
      
      const response = await fetch(`/api/models/library?${params}`);
      const data = await response.json();
      setModels(data);
    } catch (error) {
      console.error('Failed to load library:', error);
    }
    setLoading(false);
  };
  
  const searchCivitAI = async () => {
    if (!searchQuery.trim()) return;
    
    setLoading(true);
    try {
      const params = new URLSearchParams({
        query: searchQuery,
        limit: '30'
      });
      if (filterType !== 'all') params.append('model_type', filterType);
      
      const response = await fetch(`/api/models/search/civitai?${params}`);
      const data = await response.json();
      
      setModels(data.results.map((m: any) => ({
        id: m.id,
        name: m.name,
        type: m.type,
        source: 'civitai',
        description: m.description,
        thumbnail_url: m.thumbnail,
        is_downloaded: false,
        rating: m.rating,
        download_count: m.download_count,
        tags: m.tags,
        base_model: m.base_model,
      })));
    } catch (error) {
      console.error('Civit.ai search failed:', error);
    }
    setLoading(false);
  };
  
  const searchHuggingFace = async () => {
    if (!searchQuery.trim()) return;
    
    setLoading(true);
    try {
      const params = new URLSearchParams({
        query: searchQuery,
        limit: '30'
      });
      
      const response = await fetch(`/api/models/search/huggingface?${params}`);
      const data = await response.json();
      
      setModels(data.results.map((m: any) => ({
        id: m.id,
        name: m.name,
        type: 'stable-diffusion',
        source: 'huggingface',
        description: m.description,
        is_downloaded: false,
        download_count: m.downloads,
        tags: m.tags,
      })));
    } catch (error) {
      console.error('HuggingFace search failed:', error);
    }
    setLoading(false);
  };
  
  const addCivitAIModel = async (modelId: string) => {
    try {
      const response = await fetch('/api/models/add/civitai', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ model_id: modelId })
      });
      
      const data = await response.json();
      if (data.success) {
        alert(`Added: ${data.checkpoint.name}`);
        loadLibrary();
      }
    } catch (error) {
      console.error('Failed to add model:', error);
      alert('Failed to add model');
    }
  };
  
  const addCustomModel = async () => {
    if (!customUrl || !customName) {
      alert('Please provide URL and name');
      return;
    }
    
    try {
      const response = await fetch('/api/models/add/custom', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          url: customUrl,
          name: customName,
          model_type: customType,
          trigger_words: [],
          base_model: 'SD1.5'
        })
      });
      
      const data = await response.json();
      if (data.success) {
        alert(`Added: ${data.checkpoint.name}`);
        setCustomUrl('');
        setCustomName('');
        setActiveTab('library');
      }
    } catch (error) {
      console.error('Failed to add custom model:', error);
      alert('Failed to add custom model');
    }
  };
  
  const downloadModel = async (checkpointId: string) => {
    try {
      const response = await fetch(`/api/models/download/${checkpointId}`, {
        method: 'POST'
      });
      
      const data = await response.json();
      if (data.success) {
        alert('Download started! This may take several minutes.');
        // Refresh library after a delay
        setTimeout(loadLibrary, 2000);
      }
    } catch (error) {
      console.error('Download failed:', error);
      alert('Download failed');
    }
  };
  
  const deleteModel = async (checkpointId: string) => {
    if (!confirm('Are you sure you want to delete this model?')) return;
    
    try {
      const response = await fetch(`/api/models/model/${checkpointId}`, {
        method: 'DELETE'
      });
      
      const data = await response.json();
      if (data.success) {
        loadLibrary();
      }
    } catch (error) {
      console.error('Delete failed:', error);
      alert('Delete failed');
    }
  };
  
  const formatFileSize = (bytes?: number) => {
    if (!bytes) return 'Unknown';
    const gb = bytes / (1024 * 1024 * 1024);
    if (gb >= 1) return `${gb.toFixed(2)} GB`;
    const mb = bytes / (1024 * 1024);
    return `${mb.toFixed(2)} MB`;
  };
  
  return (
    <div className="model-marketplace">
      {/* Header */}
      <div className="marketplace-header">
        <h2 className="text-2xl font-bold mb-4">
          🎨 Model Marketplace
        </h2>
        <p className="text-gray-400 mb-6">
          Browse and download custom AI models from Civit.ai, HuggingFace, or add your own
        </p>
      </div>
      
      {/* Tabs */}
      <div className="tabs mb-6">
        <button
          className={`tab ${activeTab === 'library' ? 'active' : ''}`}
          onClick={() => setActiveTab('library')}
        >
          📚 My Library
        </button>
        <button
          className={`tab ${activeTab === 'civitai' ? 'active' : ''}`}
          onClick={() => setActiveTab('civitai')}
        >
          🎭 Civit.ai
        </button>
        <button
          className={`tab ${activeTab === 'huggingface' ? 'active' : ''}`}
          onClick={() => setActiveTab('huggingface')}
        >
          🤗 HuggingFace
        </button>
        <button
          className={`tab ${activeTab === 'custom' ? 'active' : ''}`}
          onClick={() => setActiveTab('custom')}
        >
          ➕ Custom URL
        </button>
      </div>
      
      {/* Search & Filters */}
      {activeTab !== 'custom' && (
        <div className="search-section mb-6">
          <div className="flex gap-4 mb-4">
            <div className="search-input-wrapper flex-1">
              <Search className="search-icon" size={20} />
              <input
                type="text"
                placeholder={
                  activeTab === 'library' 
                    ? "Filter your library..." 
                    : `Search ${activeTab}...`
                }
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                onKeyPress={(e) => {
                  if (e.key === 'Enter') {
                    if (activeTab === 'civitai') searchCivitAI();
                    else if (activeTab === 'huggingface') searchHuggingFace();
                  }
                }}
                className="search-input"
              />
            </div>
            
            {activeTab !== 'library' && (
              <button
                onClick={() => {
                  if (activeTab === 'civitai') searchCivitAI();
                  else if (activeTab === 'huggingface') searchHuggingFace();
                }}
                className="btn-primary"
                disabled={loading}
              >
                {loading ? 'Searching...' : 'Search'}
              </button>
            )}
          </div>
          
          {/* Type Filter */}
          <div className="flex gap-2 flex-wrap">
            {['all', 'stable-diffusion', 'lora', 'controlnet', 'vae', 'animatediff'].map(type => (
              <button
                key={type}
                onClick={() => setFilterType(type)}
                className={`filter-chip ${filterType === type ? 'active' : ''}`}
              >
                {type === 'all' ? 'All Types' : type.toUpperCase()}
              </button>
            ))}
          </div>
        </div>
      )}
      
      {/* Custom URL Form */}
      {activeTab === 'custom' && (
        <div className="custom-form glass-card p-6">
          <h3 className="text-xl font-semibold mb-4">Add Custom Model</h3>
          <p className="text-gray-400 mb-4">
            Provide a direct download link to a .safetensors or .ckpt file
          </p>
          
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium mb-2">Model Name</label>
              <input
                type="text"
                value={customName}
                onChange={(e) => setCustomName(e.target.value)}
                placeholder="e.g., My Custom Model"
                className="input-field w-full"
              />
            </div>
            
            <div>
              <label className="block text-sm font-medium mb-2">Download URL</label>
              <input
                type="url"
                value={customUrl}
                onChange={(e) => setCustomUrl(e.target.value)}
                placeholder="https://example.com/model.safetensors"
                className="input-field w-full"
              />
            </div>
            
            <div>
              <label className="block text-sm font-medium mb-2">Model Type</label>
              <select
                value={customType}
                onChange={(e) => setCustomType(e.target.value)}
                className="input-field w-full"
              >
                <option value="stable-diffusion">Stable Diffusion Checkpoint</option>
                <option value="lora">LoRA</option>
                <option value="controlnet">ControlNet</option>
                <option value="vae">VAE</option>
                <option value="animatediff">AnimateDiff</option>
              </select>
            </div>
            
            <button
              onClick={addCustomModel}
              className="btn-primary w-full"
            >
              Add Model
            </button>
          </div>
        </div>
      )}
      
      {/* Model Grid */}
      {activeTab !== 'custom' && (
        <div className="model-grid">
          {loading && (
            <div className="col-span-full text-center py-12">
              <div className="loading-spinner mx-auto mb-4"></div>
              <p className="text-gray-400">Loading models...</p>
            </div>
          )}
          
          {!loading && models.length === 0 && (
            <div className="col-span-full text-center py-12">
              <p className="text-gray-400 text-lg">
                {activeTab === 'library' 
                  ? 'No models in your library yet. Browse Civit.ai or HuggingFace to add some!'
                  : 'No results found. Try a different search term.'}
              </p>
            </div>
          )}
          
          {!loading && models.map((model) => (
            <div
              key={model.id}
              className={`model-card glass-card ${selectedModel?.id === model.id ? 'selected' : ''}`}
              onClick={() => setSelectedModel(model)}
            >
              {/* Thumbnail */}
              <div className="model-thumbnail">
                {model.thumbnail_url ? (
                  <img src={model.thumbnail_url} alt={model.name} />
                ) : (
                  <div className="placeholder-thumbnail">
                    <span className="text-4xl">🎨</span>
                  </div>
                )}
                
                {/* Status Badge */}
                {model.is_downloaded && (
                  <div className="status-badge downloaded">
                    <Check size={14} />
                    Downloaded
                  </div>
                )}
              </div>
              
              {/* Model Info */}
              <div className="model-info">
                <h3 className="model-name">{model.name}</h3>
                
                <div className="model-meta">
                  <span className="type-badge">{model.type}</span>
                  {model.base_model && (
                    <span className="base-badge">{model.base_model}</span>
                  )}
                </div>
                
                {model.description && (
                  <p className="model-description">
                    {model.description.substring(0, 100)}
                    {model.description.length > 100 ? '...' : ''}
                  </p>
                )}
                
                {/* Stats */}
                {(model.rating || model.download_count) && (
                  <div className="model-stats">
                    {model.rating && (
                      <span className="stat">
                        <Star size={14} fill="currentColor" />
                        {model.rating.toFixed(1)}
                      </span>
                    )}
                    {model.download_count && (
                      <span className="stat">
                        <TrendingUp size={14} />
                        {model.download_count.toLocaleString()}
                      </span>
                    )}
                  </div>
                )}
                
                {/* Tags */}
                {model.tags && model.tags.length > 0 && (
                  <div className="model-tags">
                    {model.tags.slice(0, 3).map((tag, i) => (
                      <span key={i} className="tag">{tag}</span>
                    ))}
                  </div>
                )}
                
                {/* Trigger Words */}
                {model.trigger_words && model.trigger_words.length > 0 && (
                  <div className="trigger-words">
                    <strong>Triggers:</strong> {model.trigger_words.join(', ')}
                  </div>
                )}
              </div>
              
              {/* Actions */}
              <div className="model-actions">
                {activeTab === 'library' ? (
                  <>
                    {model.is_downloaded ? (
                      <>
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            onModelSelect?.(model.id);
                          }}
                          className="btn-select"
                        >
                          Select
                        </button>
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            deleteModel(model.id);
                          }}
                          className="btn-delete"
                        >
                          <Trash2 size={16} />
                        </button>
                      </>
                    ) : (
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          downloadModel(model.id);
                        }}
                        className="btn-download"
                      >
                        <Download size={16} />
                        Download
                        {model.file_size && (
                          <span className="text-xs ml-1">
                            ({formatFileSize(model.file_size)})
                          </span>
                        )}
                      </button>
                    )}
                  </>
                ) : (
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      if (activeTab === 'civitai') {
                        addCivitAIModel(model.id);
                      }
                    }}
                    className="btn-add"
                  >
                    Add to Library
                  </button>
                )}
              </div>
            </div>
          ))}
        </div>
      )}
      
      <style jsx>{`
        .model-marketplace {
          padding: 20px;
        }
        
        .tabs {
          display: flex;
          gap: 8px;
          border-bottom: 2px solid rgba(255, 255, 255, 0.1);
        }
        
        .tab {
          padding: 12px 24px;
          background: transparent;
          border: none;
          color: rgba(255, 255, 255, 0.6);
          font-weight: 500;
          cursor: pointer;
          transition: all 0.2s;
          border-bottom: 2px solid transparent;
          margin-bottom: -2px;
        }
        
        .tab:hover {
          color: rgba(255, 255, 255, 0.9);
        }
        
        .tab.active {
          color: #9333ea;
          border-bottom-color: #9333ea;
        }
        
        .search-section {
          margin-top: 24px;
        }
        
        .search-input-wrapper {
          position: relative;
        }
        
        .search-icon {
          position: absolute;
          left: 16px;
          top: 50%;
          transform: translateY(-50%);
          color: rgba(255, 255, 255, 0.4);
        }
        
        .search-input {
          width: 100%;
          padding: 12px 16px 12px 48px;
          background: rgba(255, 255, 255, 0.05);
          border: 1px solid rgba(255, 255, 255, 0.1);
          border-radius: 12px;
          color: white;
          font-size: 16px;
        }
        
        .search-input:focus {
          outline: none;
          border-color: #9333ea;
          box-shadow: 0 0 0 3px rgba(147, 51, 234, 0.1);
        }
        
        .filter-chip {
          padding: 8px 16px;
          background: rgba(255, 255, 255, 0.05);
          border: 1px solid rgba(255, 255, 255, 0.1);
          border-radius: 20px;
          color: rgba(255, 255, 255, 0.7);
          font-size: 14px;
          cursor: pointer;
          transition: all 0.2s;
        }
        
        .filter-chip:hover {
          background: rgba(255, 255, 255, 0.1);
          color: white;
        }
        
        .filter-chip.active {
          background: linear-gradient(135deg, #9333ea, #06b6d4);
          border-color: transparent;
          color: white;
        }
        
        .model-grid {
          display: grid;
          grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
          gap: 20px;
          margin-top: 24px;
        }
        
        .model-card {
          cursor: pointer;
          transition: all 0.3s;
          overflow: hidden;
        }
        
        .model-card:hover {
          transform: translateY(-4px);
          box-shadow: 0 8px 32px rgba(147, 51, 234, 0.3);
        }
        
        .model-card.selected {
          border-color: #9333ea;
          box-shadow: 0 0 0 2px #9333ea;
        }
        
        .model-thumbnail {
          position: relative;
          width: 100%;
          height: 200px;
          overflow: hidden;
          background: rgba(0, 0, 0, 0.3);
          border-radius: 12px 12px 0 0;
        }
        
        .model-thumbnail img {
          width: 100%;
          height: 100%;
          object-fit: cover;
        }
        
        .placeholder-thumbnail {
          width: 100%;
          height: 100%;
          display: flex;
          align-items: center;
          justify-content: center;
          background: linear-gradient(135deg, #1a1a2e, #2d2d44);
        }
        
        .status-badge {
          position: absolute;
          top: 12px;
          right: 12px;
          padding: 6px 12px;
          border-radius: 20px;
          font-size: 12px;
          font-weight: 600;
          display: flex;
          align-items: center;
          gap: 4px;
        }
        
        .status-badge.downloaded {
          background: rgba(34, 197, 94, 0.9);
          color: white;
        }
        
        .model-info {
          padding: 16px;
        }
        
        .model-name {
          font-size: 16px;
          font-weight: 600;
          margin-bottom: 8px;
          color: white;
          display: -webkit-box;
          -webkit-line-clamp: 2;
          -webkit-box-orient: vertical;
          overflow: hidden;
        }
        
        .model-meta {
          display: flex;
          gap: 8px;
          margin-bottom: 8px;
          flex-wrap: wrap;
        }
        
        .type-badge, .base-badge {
          padding: 4px 8px;
          border-radius: 6px;
          font-size: 11px;
          font-weight: 600;
          text-transform: uppercase;
        }
        
        .type-badge {
          background: rgba(147, 51, 234, 0.2);
          color: #c084fc;
        }
        
        .base-badge {
          background: rgba(6, 182, 212, 0.2);
          color: #67e8f9;
        }
        
        .model-description {
          font-size: 13px;
          color: rgba(255, 255, 255, 0.6);
          line-height: 1.5;
          margin-bottom: 8px;
        }
        
        .model-stats {
          display: flex;
          gap: 16px;
          margin-bottom: 8px;
        }
        
        .stat {
          display: flex;
          align-items: center;
          gap: 4px;
          font-size: 13px;
          color: rgba(255, 255, 255, 0.7);
        }
        
        .model-tags {
          display: flex;
          gap: 6px;
          flex-wrap: wrap;
          margin-bottom: 12px;
        }
        
        .tag {
          padding: 3px 8px;
          background: rgba(255, 255, 255, 0.05);
          border-radius: 4px;
          font-size: 11px;
          color: rgba(255, 255, 255, 0.5);
        }
        
        .trigger-words {
          font-size: 12px;
          color: rgba(255, 255, 255, 0.6);
          margin-bottom: 12px;
        }
        
        .model-actions {
          padding: 0 16px 16px;
          display: flex;
          gap: 8px;
        }
        
        .btn-select, .btn-download, .btn-add, .btn-delete {
          flex: 1;
          padding: 10px;
          border: none;
          border-radius: 8px;
          font-weight: 600;
          cursor: pointer;
          transition: all 0.2s;
          display: flex;
          align-items: center;
          justify-content: center;
          gap: 6px;
        }
        
        .btn-select {
          background: linear-gradient(135deg, #9333ea, #06b6d4);
          color: white;
        }
        
        .btn-select:hover {
          transform: scale(1.02);
          box-shadow: 0 4px 12px rgba(147, 51, 234, 0.4);
        }
        
        .btn-download, .btn-add {
          background: rgba(59, 130, 246, 0.9);
          color: white;
        }
        
        .btn-download:hover, .btn-add:hover {
          background: rgba(59, 130, 246, 1);
        }
        
        .btn-delete {
          flex: 0 0 auto;
          background: rgba(239, 68, 68, 0.2);
          color: #ef4444;
        }
        
        .btn-delete:hover {
          background: rgba(239, 68, 68, 0.9);
          color: white;
        }
        
        .custom-form {
          max-width: 600px;
          margin: 0 auto;
        }
        
        .input-field {
          padding: 12px;
          background: rgba(255, 255, 255, 0.05);
          border: 1px solid rgba(255, 255, 255, 0.1);
          border-radius: 8px;
          color: white;
          font-size: 14px;
        }
        
        .input-field:focus {
          outline: none;
          border-color: #9333ea;
          box-shadow: 0 0 0 3px rgba(147, 51, 234, 0.1);
        }
        
        .loading-spinner {
          width: 48px;
          height: 48px;
          border: 4px solid rgba(255, 255, 255, 0.1);
          border-top-color: #9333ea;
          border-radius: 50%;
          animation: spin 1s linear infinite;
        }
        
        @keyframes spin {
          to { transform: rotate(360deg); }
        }
      `}</style>
    </div>
  );
}
