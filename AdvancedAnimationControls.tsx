/**
 * Advanced Animation Controls
 * Deforum-style keyframe editor with timeline, camera controls, and prompt scheduling
 */

import React, { useState, useRef, useEffect } from 'react';
import { 
  Play, Pause, Plus, Trash2, Copy, Camera, Layers, Zap, 
  RotateCw, Move, ZoomIn, Sliders, Wand2 
} from 'lucide-react';

interface Keyframe {
  frame: number;
  prompt: string;
  negative_prompt: string;
  strength: number;
  seed: number;
  zoom: number;
  angle: number;
  translation_x: number;
  translation_y: number;
  translation_z: number;
  rotation_3d_x: number;
  rotation_3d_y: number;
  rotation_3d_z: number;
}

interface AdvancedAnimationControlsProps {
  totalFrames: number;
  fps: number;
  onKeyframesChange: (keyframes: Keyframe[]) => void;
  onGenerate: () => void;
}

export default function AdvancedAnimationControls({
  totalFrames,
  fps,
  onKeyframesChange,
  onGenerate
}: AdvancedAnimationControlsProps) {
  const [keyframes, setKeyframes] = useState<Keyframe[]>([
    {
      frame: 0,
      prompt: '',
      negative_prompt: 'blurry, bad quality, distorted',
      strength: 0.75,
      seed: -1,
      zoom: 1.0,
      angle: 0,
      translation_x: 0,
      translation_y: 0,
      translation_z: 0,
      rotation_3d_x: 0,
      rotation_3d_y: 0,
      rotation_3d_z: 0,
    }
  ]);
  
  const [selectedKeyframeIndex, setSelectedKeyframeIndex] = useState(0);
  const [currentFrame, setCurrentFrame] = useState(0);
  const [isPlaying, setIsPlaying] = useState(false);
  const [activeTab, setActiveTab] = useState<'prompts' | 'camera' | 'advanced'>('prompts');
  const [animationMode, setAnimationMode] = useState<'2D' | '3D'>('3D');
  
  const timelineRef = useRef<HTMLDivElement>(null);
  const playbackInterval = useRef<NodeJS.Timeout | null>(null);
  
  useEffect(() => {
    onKeyframesChange(keyframes);
  }, [keyframes]);
  
  useEffect(() => {
    if (isPlaying) {
      playbackInterval.current = setInterval(() => {
        setCurrentFrame(prev => {
          if (prev >= totalFrames - 1) {
            setIsPlaying(false);
            return 0;
          }
          return prev + 1;
        });
      }, 1000 / fps);
    } else if (playbackInterval.current) {
      clearInterval(playbackInterval.current);
    }
    
    return () => {
      if (playbackInterval.current) clearInterval(playbackInterval.current);
    };
  }, [isPlaying, totalFrames, fps]);
  
  const selectedKeyframe = keyframes[selectedKeyframeIndex];
  
  const addKeyframe = () => {
    const newKeyframe: Keyframe = {
      ...selectedKeyframe,
      frame: currentFrame,
    };
    
    const newKeyframes = [...keyframes, newKeyframe].sort((a, b) => a.frame - b.frame);
    setKeyframes(newKeyframes);
    setSelectedKeyframeIndex(newKeyframes.findIndex(kf => kf.frame === currentFrame));
  };
  
  const deleteKeyframe = (index: number) => {
    if (keyframes.length <= 1) {
      alert('Cannot delete the last keyframe');
      return;
    }
    
    const newKeyframes = keyframes.filter((_, i) => i !== index);
    setKeyframes(newKeyframes);
    setSelectedKeyframeIndex(Math.max(0, index - 1));
  };
  
  const duplicateKeyframe = (index: number) => {
    const newKeyframe = { ...keyframes[index], frame: currentFrame };
    const newKeyframes = [...keyframes, newKeyframe].sort((a, b) => a.frame - b.frame);
    setKeyframes(newKeyframes);
  };
  
  const updateKeyframe = (updates: Partial<Keyframe>) => {
    const newKeyframes = [...keyframes];
    newKeyframes[selectedKeyframeIndex] = {
      ...newKeyframes[selectedKeyframeIndex],
      ...updates
    };
    setKeyframes(newKeyframes);
  };
  
  const generateSchedule = (param: string, start: number, end: number) => {
    // Generate smooth schedule between keyframes
    const schedule = `0:(${start}), ${totalFrames}:(${end})`;
    return schedule;
  };
  
  const loadPreset = (preset: string) => {
    let presetKeyframes: Keyframe[] = [];
    
    switch (preset) {
      case 'zoom_in':
        presetKeyframes = [
          { ...keyframes[0], frame: 0, zoom: 1.0 },
          { ...keyframes[0], frame: totalFrames - 1, zoom: 1.5 }
        ];
        break;
        
      case 'rotate_360':
        presetKeyframes = [
          { ...keyframes[0], frame: 0, rotation_3d_y: 0 },
          { ...keyframes[0], frame: totalFrames - 1, rotation_3d_y: 360 }
        ];
        break;
        
      case 'pan_left':
        presetKeyframes = [
          { ...keyframes[0], frame: 0, translation_x: 0 },
          { ...keyframes[0], frame: totalFrames - 1, translation_x: -50 }
        ];
        break;
        
      case 'dolly_forward':
        presetKeyframes = [
          { ...keyframes[0], frame: 0, translation_z: 0 },
          { ...keyframes[0], frame: totalFrames - 1, translation_z: 50 }
        ];
        break;
    }
    
    if (presetKeyframes.length > 0) {
      setKeyframes(presetKeyframes);
    }
  };
  
  const formatTime = (frame: number) => {
    const seconds = frame / fps;
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    const ms = Math.floor((seconds % 1) * 100);
    return `${mins}:${secs.toString().padStart(2, '0')}.${ms.toString().padStart(2, '0')}`;
  };
  
  return (
    <div className="advanced-animation-controls">
      <div className="controls-header">
        <h3 className="text-xl font-bold flex items-center gap-2">
          <Camera size={24} />
          Advanced Animation Controls
        </h3>
        <p className="text-sm text-gray-400 mt-1">
          Deforum-style keyframe animation with camera controls and prompt scheduling
        </p>
      </div>
      
      {/* Timeline */}
      <div className="timeline-section glass-card mt-4 p-4">
        <div className="timeline-header mb-3">
          <div className="flex justify-between items-center">
            <div className="flex items-center gap-3">
              <button
                onClick={() => setIsPlaying(!isPlaying)}
                className="playback-btn"
              >
                {isPlaying ? <Pause size={18} /> : <Play size={18} />}
              </button>
              
              <span className="time-display">
                {formatTime(currentFrame)} / {formatTime(totalFrames)}
              </span>
              
              <span className="frame-display">
                Frame {currentFrame} / {totalFrames}
              </span>
            </div>
            
            <button
              onClick={addKeyframe}
              className="btn-add-keyframe"
            >
              <Plus size={16} />
              Add Keyframe
            </button>
          </div>
        </div>
        
        {/* Timeline Track */}
        <div
          ref={timelineRef}
          className="timeline-track"
          onClick={(e) => {
            const rect = e.currentTarget.getBoundingClientRect();
            const x = e.clientX - rect.left;
            const frame = Math.floor((x / rect.width) * totalFrames);
            setCurrentFrame(Math.max(0, Math.min(totalFrames - 1, frame)));
          }}
        >
          {/* Keyframe Markers */}
          {keyframes.map((kf, index) => (
            <div
              key={index}
              className={`keyframe-marker ${selectedKeyframeIndex === index ? 'selected' : ''}`}
              style={{ left: `${(kf.frame / totalFrames) * 100}%` }}
              onClick={(e) => {
                e.stopPropagation();
                setSelectedKeyframeIndex(index);
                setCurrentFrame(kf.frame);
              }}
              title={`Frame ${kf.frame}: ${kf.prompt.substring(0, 30)}...`}
            >
              <div className="marker-dot"></div>
              <div className="marker-label">{kf.frame}</div>
            </div>
          ))}
          
          {/* Current Frame Indicator */}
          <div
            className="current-frame-indicator"
            style={{ left: `${(currentFrame / totalFrames) * 100}%` }}
          />
        </div>
        
        {/* Frame Scrubber */}
        <input
          type="range"
          min="0"
          max={totalFrames - 1}
          value={currentFrame}
          onChange={(e) => setCurrentFrame(parseInt(e.target.value))}
          className="frame-scrubber"
        />
      </div>
      
      {/* Keyframe List */}
      <div className="keyframe-list glass-card mt-4 p-4">
        <h4 className="font-semibold mb-3 flex items-center gap-2">
          <Layers size={18} />
          Keyframes ({keyframes.length})
        </h4>
        
        <div className="keyframe-items">
          {keyframes.map((kf, index) => (
            <div
              key={index}
              className={`keyframe-item ${selectedKeyframeIndex === index ? 'selected' : ''}`}
              onClick={() => {
                setSelectedKeyframeIndex(index);
                setCurrentFrame(kf.frame);
              }}
            >
              <div className="keyframe-item-header">
                <span className="keyframe-number">#{index + 1}</span>
                <span className="keyframe-frame">Frame {kf.frame}</span>
                <span className="keyframe-time">{formatTime(kf.frame)}</span>
                
                <div className="keyframe-actions">
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      duplicateKeyframe(index);
                    }}
                    className="action-btn"
                    title="Duplicate"
                  >
                    <Copy size={14} />
                  </button>
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      deleteKeyframe(index);
                    }}
                    className="action-btn delete"
                    title="Delete"
                  >
                    <Trash2 size={14} />
                  </button>
                </div>
              </div>
              
              <div className="keyframe-prompt">
                {kf.prompt || <span className="text-gray-500">No prompt</span>}
              </div>
            </div>
          ))}
        </div>
      </div>
      
      {/* Keyframe Editor */}
      <div className="keyframe-editor glass-card mt-4 p-4">
        <h4 className="font-semibold mb-4">
          Edit Keyframe #{selectedKeyframeIndex + 1} (Frame {selectedKeyframe.frame})
        </h4>
        
        {/* Tabs */}
        <div className="editor-tabs mb-4">
          <button
            className={`editor-tab ${activeTab === 'prompts' ? 'active' : ''}`}
            onClick={() => setActiveTab('prompts')}
          >
            <Wand2 size={16} />
            Prompts
          </button>
          <button
            className={`editor-tab ${activeTab === 'camera' ? 'active' : ''}`}
            onClick={() => setActiveTab('camera')}
          >
            <Camera size={16} />
            Camera
          </button>
          <button
            className={`editor-tab ${activeTab === 'advanced' ? 'active' : ''}`}
            onClick={() => setActiveTab('advanced')}
          >
            <Sliders size={16} />
            Advanced
          </button>
        </div>
        
        {/* Prompts Tab */}
        {activeTab === 'prompts' && (
          <div className="prompts-editor">
            <div className="form-group">
              <label>Prompt</label>
              <textarea
                value={selectedKeyframe.prompt}
                onChange={(e) => updateKeyframe({ prompt: e.target.value })}
                placeholder="Describe what you want to generate at this keyframe..."
                rows={4}
                className="textarea-field"
              />
              <div className="field-hint">
                Use (word:1.2) for emphasis, [word] for de-emphasis
              </div>
            </div>
            
            <div className="form-group">
              <label>Negative Prompt</label>
              <textarea
                value={selectedKeyframe.negative_prompt}
                onChange={(e) => updateKeyframe({ negative_prompt: e.target.value })}
                placeholder="What to avoid..."
                rows={2}
                className="textarea-field"
              />
            </div>
            
            <div className="form-row">
              <div className="form-group">
                <label>Strength</label>
                <input
                  type="range"
                  min="0"
                  max="1"
                  step="0.05"
                  value={selectedKeyframe.strength}
                  onChange={(e) => updateKeyframe({ strength: parseFloat(e.target.value) })}
                  className="slider-field"
                />
                <span className="slider-value">{selectedKeyframe.strength.toFixed(2)}</span>
              </div>
              
              <div className="form-group">
                <label>Seed</label>
                <input
                  type="number"
                  value={selectedKeyframe.seed}
                  onChange={(e) => updateKeyframe({ seed: parseInt(e.target.value) })}
                  placeholder="-1 for random"
                  className="input-field"
                />
              </div>
            </div>
          </div>
        )}
        
        {/* Camera Tab */}
        {activeTab === 'camera' && (
          <div className="camera-editor">
            {/* Animation Mode */}
            <div className="form-group mb-4">
              <label>Animation Mode</label>
              <div className="mode-selector">
                <button
                  className={`mode-btn ${animationMode === '2D' ? 'active' : ''}`}
                  onClick={() => setAnimationMode('2D')}
                >
                  2D Transform
                </button>
                <button
                  className={`mode-btn ${animationMode === '3D' ? 'active' : ''}`}
                  onClick={() => setAnimationMode('3D')}
                >
                  3D Camera
                </button>
              </div>
            </div>
            
            {/* Camera Presets */}
            <div className="form-group mb-4">
              <label>Quick Presets</label>
              <div className="preset-buttons">
                <button onClick={() => loadPreset('zoom_in')} className="preset-btn">
                  <ZoomIn size={14} /> Zoom In
                </button>
                <button onClick={() => loadPreset('rotate_360')} className="preset-btn">
                  <RotateCw size={14} /> Rotate 360°
                </button>
                <button onClick={() => loadPreset('pan_left')} className="preset-btn">
                  <Move size={14} /> Pan Left
                </button>
                <button onClick={() => loadPreset('dolly_forward')} className="preset-btn">
                  <Zap size={14} /> Dolly Forward
                </button>
              </div>
            </div>
            
            {/* 2D Controls */}
            {animationMode === '2D' && (
              <div className="controls-2d">
                <div className="form-group">
                  <label>Zoom</label>
                  <input
                    type="range"
                    min="0.5"
                    max="2"
                    step="0.01"
                    value={selectedKeyframe.zoom}
                    onChange={(e) => updateKeyframe({ zoom: parseFloat(e.target.value) })}
                    className="slider-field"
                  />
                  <span className="slider-value">{selectedKeyframe.zoom.toFixed(2)}x</span>
                </div>
                
                <div className="form-group">
                  <label>Rotation (degrees)</label>
                  <input
                    type="range"
                    min="-180"
                    max="180"
                    step="1"
                    value={selectedKeyframe.angle}
                    onChange={(e) => updateKeyframe({ angle: parseFloat(e.target.value) })}
                    className="slider-field"
                  />
                  <span className="slider-value">{selectedKeyframe.angle.toFixed(0)}°</span>
                </div>
                
                <div className="form-row">
                  <div className="form-group">
                    <label>Pan X</label>
                    <input
                      type="number"
                      value={selectedKeyframe.translation_x}
                      onChange={(e) => updateKeyframe({ translation_x: parseFloat(e.target.value) })}
                      className="input-field"
                      step="1"
                    />
                  </div>
                  
                  <div className="form-group">
                    <label>Pan Y</label>
                    <input
                      type="number"
                      value={selectedKeyframe.translation_y}
                      onChange={(e) => updateKeyframe({ translation_y: parseFloat(e.target.value) })}
                      className="input-field"
                      step="1"
                    />
                  </div>
                </div>
              </div>
            )}
            
            {/* 3D Controls */}
            {animationMode === '3D' && (
              <div className="controls-3d">
                <div className="form-group">
                  <label>Translation Z (Depth)</label>
                  <input
                    type="range"
                    min="-100"
                    max="100"
                    step="1"
                    value={selectedKeyframe.translation_z}
                    onChange={(e) => updateKeyframe({ translation_z: parseFloat(e.target.value) })}
                    className="slider-field"
                  />
                  <span className="slider-value">{selectedKeyframe.translation_z.toFixed(0)}</span>
                </div>
                
                <div className="form-group">
                  <label>Rotation X (Pitch)</label>
                  <input
                    type="range"
                    min="-180"
                    max="180"
                    step="1"
                    value={selectedKeyframe.rotation_3d_x}
                    onChange={(e) => updateKeyframe({ rotation_3d_x: parseFloat(e.target.value) })}
                    className="slider-field"
                  />
                  <span className="slider-value">{selectedKeyframe.rotation_3d_x.toFixed(0)}°</span>
                </div>
                
                <div className="form-group">
                  <label>Rotation Y (Yaw)</label>
                  <input
                    type="range"
                    min="-180"
                    max="180"
                    step="1"
                    value={selectedKeyframe.rotation_3d_y}
                    onChange={(e) => updateKeyframe({ rotation_3d_y: parseFloat(e.target.value) })}
                    className="slider-field"
                  />
                  <span className="slider-value">{selectedKeyframe.rotation_3d_y.toFixed(0)}°</span>
                </div>
                
                <div className="form-group">
                  <label>Rotation Z (Roll)</label>
                  <input
                    type="range"
                    min="-180"
                    max="180"
                    step="1"
                    value={selectedKeyframe.rotation_3d_z}
                    onChange={(e) => updateKeyframe({ rotation_3d_z: parseFloat(e.target.value) })}
                    className="slider-field"
                  />
                  <span className="slider-value">{selectedKeyframe.rotation_3d_z.toFixed(0)}°</span>
                </div>
              </div>
            )}
          </div>
        )}
        
        {/* Advanced Tab */}
        {activeTab === 'advanced' && (
          <div className="advanced-editor">
            <div className="form-group">
              <label>Frame Number</label>
              <input
                type="number"
                min="0"
                max={totalFrames - 1}
                value={selectedKeyframe.frame}
                onChange={(e) => {
                  const newFrame = parseInt(e.target.value);
                  updateKeyframe({ frame: newFrame });
                  setCurrentFrame(newFrame);
                }}
                className="input-field"
              />
            </div>
            
            <div className="info-box mt-4">
              <h5 className="font-semibold mb-2">💡 Tips</h5>
              <ul className="text-sm space-y-1 text-gray-400">
                <li>• Values between keyframes are automatically interpolated</li>
                <li>• Use seed = -1 for random variation between frames</li>
                <li>• Lower strength = more morphing, higher = more stable</li>
                <li>• 3D rotations work best with lower diffusion cadence</li>
              </ul>
            </div>
          </div>
        )}
      </div>
      
      {/* Generate Button */}
      <button
        onClick={onGenerate}
        className="btn-generate mt-6"
      >
        <Zap size={20} />
        Generate AI Animation
      </button>
      
      <style jsx>{`
        .advanced-animation-controls {
          margin-top: 24px;
        }
        
        .timeline-section {
          background: rgba(0, 0, 0, 0.3);
        }
        
        .playback-btn {
          width: 40px;
          height: 40px;
          border-radius: 50%;
          background: linear-gradient(135deg, #9333ea, #06b6d4);
          border: none;
          color: white;
          display: flex;
          align-items: center;
          justify-content: center;
          cursor: pointer;
          transition: all 0.2s;
        }
        
        .playback-btn:hover {
          transform: scale(1.1);
          box-shadow: 0 4px 12px rgba(147, 51, 234, 0.4);
        }
        
        .time-display, .frame-display {
          font-family: 'Courier New', monospace;
          font-size: 14px;
          color: rgba(255, 255, 255, 0.8);
        }
        
        .btn-add-keyframe {
          padding: 8px 16px;
          background: rgba(34, 197, 94, 0.2);
          border: 1px solid rgba(34, 197, 94, 0.4);
          border-radius: 8px;
          color: #22c55e;
          font-weight: 600;
          display: flex;
          align-items: center;
          gap: 6px;
          cursor: pointer;
          transition: all 0.2s;
        }
        
        .btn-add-keyframe:hover {
          background: rgba(34, 197, 94, 0.3);
        }
        
        .timeline-track {
          position: relative;
          height: 60px;
          background: rgba(255, 255, 255, 0.05);
          border-radius: 8px;
          margin: 16px 0;
          cursor: pointer;
        }
        
        .keyframe-marker {
          position: absolute;
          top: 50%;
          transform: translate(-50%, -50%);
          cursor: pointer;
          z-index: 2;
        }
        
        .marker-dot {
          width: 12px;
          height: 12px;
          background: #9333ea;
          border: 2px solid white;
          border-radius: 50%;
          transition: all 0.2s;
        }
        
        .keyframe-marker:hover .marker-dot {
          transform: scale(1.3);
          box-shadow: 0 0 12px rgba(147, 51, 234, 0.6);
        }
        
        .keyframe-marker.selected .marker-dot {
          width: 16px;
          height: 16px;
          background: #06b6d4;
          box-shadow: 0 0 16px rgba(6, 182, 212, 0.8);
        }
        
        .marker-label {
          position: absolute;
          top: -24px;
          left: 50%;
          transform: translateX(-50%);
          font-size: 11px;
          color: rgba(255, 255, 255, 0.6);
          white-space: nowrap;
        }
        
        .current-frame-indicator {
          position: absolute;
          top: 0;
          bottom: 0;
          width: 2px;
          background: #ef4444;
          box-shadow: 0 0 8px rgba(239, 68, 68, 0.6);
          pointer-events: none;
          z-index: 3;
        }
        
        .frame-scrubber {
          width: 100%;
          height: 6px;
          -webkit-appearance: none;
          appearance: none;
          background: rgba(255, 255, 255, 0.1);
          border-radius: 3px;
          outline: none;
        }
        
        .frame-scrubber::-webkit-slider-thumb {
          -webkit-appearance: none;
          appearance: none;
          width: 16px;
          height: 16px;
          background: #9333ea;
          border-radius: 50%;
          cursor: pointer;
        }
        
        .keyframe-items {
          max-height: 300px;
          overflow-y: auto;
          display: flex;
          flex-direction: column;
          gap: 8px;
        }
        
        .keyframe-item {
          padding: 12px;
          background: rgba(255, 255, 255, 0.03);
          border: 1px solid rgba(255, 255, 255, 0.1);
          border-radius: 8px;
          cursor: pointer;
          transition: all 0.2s;
        }
        
        .keyframe-item:hover {
          background: rgba(255, 255, 255, 0.06);
          border-color: rgba(147, 51, 234, 0.3);
        }
        
        .keyframe-item.selected {
          background: rgba(147, 51, 234, 0.1);
          border-color: #9333ea;
        }
        
        .keyframe-item-header {
          display: flex;
          align-items: center;
          gap: 12px;
          margin-bottom: 8px;
        }
        
        .keyframe-number {
          font-weight: 700;
          color: #9333ea;
        }
        
        .keyframe-frame, .keyframe-time {
          font-size: 13px;
          color: rgba(255, 255, 255, 0.6);
        }
        
        .keyframe-actions {
          margin-left: auto;
          display: flex;
          gap: 4px;
        }
        
        .action-btn {
          padding: 4px 8px;
          background: rgba(255, 255, 255, 0.05);
          border: none;
          border-radius: 4px;
          color: rgba(255, 255, 255, 0.6);
          cursor: pointer;
          transition: all 0.2s;
        }
        
        .action-btn:hover {
          background: rgba(255, 255, 255, 0.1);
          color: white;
        }
        
        .action-btn.delete:hover {
          background: rgba(239, 68, 68, 0.2);
          color: #ef4444;
        }
        
        .keyframe-prompt {
          font-size: 13px;
          color: rgba(255, 255, 255, 0.8);
          line-height: 1.4;
        }
        
        .editor-tabs {
          display: flex;
          gap: 8px;
          border-bottom: 2px solid rgba(255, 255, 255, 0.1);
        }
        
        .editor-tab {
          padding: 10px 20px;
          background: transparent;
          border: none;
          color: rgba(255, 255, 255, 0.6);
          font-weight: 500;
          display: flex;
          align-items: center;
          gap: 8px;
          cursor: pointer;
          transition: all 0.2s;
          border-bottom: 2px solid transparent;
          margin-bottom: -2px;
        }
        
        .editor-tab:hover {
          color: rgba(255, 255, 255, 0.9);
        }
        
        .editor-tab.active {
          color: #9333ea;
          border-bottom-color: #9333ea;
        }
        
        .form-group {
          margin-bottom: 16px;
        }
        
        .form-group label {
          display: block;
          font-size: 13px;
          font-weight: 600;
          margin-bottom: 8px;
          color: rgba(255, 255, 255, 0.8);
        }
        
        .textarea-field, .input-field {
          width: 100%;
          padding: 10px;
          background: rgba(255, 255, 255, 0.05);
          border: 1px solid rgba(255, 255, 255, 0.1);
          border-radius: 8px;
          color: white;
          font-size: 14px;
          font-family: inherit;
        }
        
        .textarea-field:focus, .input-field:focus {
          outline: none;
          border-color: #9333ea;
          box-shadow: 0 0 0 3px rgba(147, 51, 234, 0.1);
        }
        
        .field-hint {
          font-size: 12px;
          color: rgba(255, 255, 255, 0.4);
          margin-top: 4px;
        }
        
        .form-row {
          display: grid;
          grid-template-columns: 1fr 1fr;
          gap: 16px;
        }
        
        .slider-field {
          width: 100%;
          -webkit-appearance: none;
          appearance: none;
          height: 6px;
          background: rgba(255, 255, 255, 0.1);
          border-radius: 3px;
          outline: none;
        }
        
        .slider-field::-webkit-slider-thumb {
          -webkit-appearance: none;
          appearance: none;
          width: 18px;
          height: 18px;
          background: linear-gradient(135deg, #9333ea, #06b6d4);
          border-radius: 50%;
          cursor: pointer;
        }
        
        .slider-value {
          display: inline-block;
          margin-left: 12px;
          font-size: 14px;
          font-weight: 600;
          color: #9333ea;
        }
        
        .mode-selector {
          display: flex;
          gap: 8px;
        }
        
        .mode-btn {
          flex: 1;
          padding: 12px;
          background: rgba(255, 255, 255, 0.05);
          border: 1px solid rgba(255, 255, 255, 0.1);
          border-radius: 8px;
          color: rgba(255, 255, 255, 0.7);
          font-weight: 600;
          cursor: pointer;
          transition: all 0.2s;
        }
        
        .mode-btn:hover {
          background: rgba(255, 255, 255, 0.1);
          color: white;
        }
        
        .mode-btn.active {
          background: linear-gradient(135deg, #9333ea, #06b6d4);
          border-color: transparent;
          color: white;
        }
        
        .preset-buttons {
          display: grid;
          grid-template-columns: repeat(2, 1fr);
          gap: 8px;
        }
        
        .preset-btn {
          padding: 10px;
          background: rgba(6, 182, 212, 0.1);
          border: 1px solid rgba(6, 182, 212, 0.3);
          border-radius: 8px;
          color: #06b6d4;
          font-size: 13px;
          font-weight: 600;
          display: flex;
          align-items: center;
          justify-content: center;
          gap: 6px;
          cursor: pointer;
          transition: all 0.2s;
        }
        
        .preset-btn:hover {
          background: rgba(6, 182, 212, 0.2);
          transform: translateY(-2px);
        }
        
        .info-box {
          padding: 16px;
          background: rgba(59, 130, 246, 0.1);
          border: 1px solid rgba(59, 130, 246, 0.2);
          border-radius: 8px;
        }
        
        .btn-generate {
          width: 100%;
          padding: 16px;
          background: linear-gradient(135deg, #9333ea, #06b6d4);
          border: none;
          border-radius: 12px;
          color: white;
          font-size: 18px;
          font-weight: 700;
          display: flex;
          align-items: center;
          justify-content: center;
          gap: 12px;
          cursor: pointer;
          transition: all 0.3s;
        }
        
        .btn-generate:hover {
          transform: translateY(-2px);
          box-shadow: 0 12px 32px rgba(147, 51, 234, 0.4);
        }
      `}</style>
    </div>
  );
}
