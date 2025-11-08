import { useState, useEffect, useCallback, useRef } from 'react'
import Head from 'next/head'
import axios from 'axios'
import { useDropzone } from 'react-dropzone'
import { motion, AnimatePresence } from 'framer-motion'
import { 
  FiUpload, FiMusic, FiImage, FiPlay, FiDownload, 
  FiSettings, FiZap, FiVideo, FiRefreshCw, FiCheck,
  FiAlertCircle, FiX 
} from 'react-icons/fi'

// Types
interface Project {
  project_id: string
  status: string
  progress: number
  message: string
  output_url?: string
}

interface AnimationConfig {
  project_id: string
  style_prompt: string
  motion_intensity: number
  zoom_effect: string
  rotation: string
  color_grading: string
  fps: number
  duration?: number
  interpolation: string
  audio_reactivity: string
  audio_frequency: string
  coherence: number
  seed?: number
  resolution: string
  quality_preset: string
  motion_blur: boolean
  depth_effect: boolean
  particle_effects: boolean
  output_format: string
}

export default function Home() {
  // State management
  const [projectId, setProjectId] = useState<string | null>(null)
  const [uploadedImages, setUploadedImages] = useState<File[]>([])
  const [uploadedAudio, setUploadedAudio] = useState<File | null>(null)
  const [projectStatus, setProjectStatus] = useState<Project | null>(null)
  const [isGenerating, setIsGenerating] = useState(false)
  const [showAdvanced, setShowAdvanced] = useState(false)
  const [selectedPreset, setSelectedPreset] = useState<string>('Music Video')
  const [ws, setWs] = useState<WebSocket | null>(null)

  // Configuration state
  const [config, setConfig] = useState<Partial<AnimationConfig>>({
    style_prompt: 'music video, dynamic camera, high energy, professional production',
    motion_intensity: 0.7,
    zoom_effect: 'pulse',
    rotation: 'none',
    color_grading: 'vibrant',
    fps: 30,
    interpolation: 'ease-in-out',
    audio_reactivity: 'high',
    audio_frequency: 'all',
    coherence: 0.7,
    resolution: '1080p',
    quality_preset: 'balanced',
    motion_blur: false,
    depth_effect: false,
    particle_effects: false,
    output_format: 'mp4'
  })

  // Style presets
  const stylePresets = [
    {
      name: 'Cinematic',
      prompt: 'cinematic lighting, film grain, anamorphic, professional color grading',
      settings: { color_grading: 'neutral', motion_blur: true, motion_intensity: 0.5 }
    },
    {
      name: 'Anime',
      prompt: 'anime style, vibrant colors, cel shading, Studio Ghibli inspired',
      settings: { color_grading: 'vibrant', motion_intensity: 0.6 }
    },
    {
      name: 'Cyberpunk',
      prompt: 'cyberpunk, neon lights, dystopian, futuristic, blade runner aesthetic',
      settings: { color_grading: 'cool', particle_effects: true, motion_intensity: 0.7 }
    },
    {
      name: 'Music Video',
      prompt: 'music video, dynamic camera, high energy, professional production',
      settings: { audio_reactivity: 'high', motion_intensity: 0.7, color_grading: 'vibrant' }
    },
    {
      name: 'Psychedelic',
      prompt: 'psychedelic, trippy, kaleidoscopic, vibrant colors, fluid motion',
      settings: { motion_intensity: 0.9, particle_effects: true, color_grading: 'vibrant' }
    }
  ]

  // Create project on mount
  useEffect(() => {
    createProject()
  }, [])

  // WebSocket connection
  useEffect(() => {
    if (projectId && isGenerating) {
      const websocket = new WebSocket(`ws://localhost:8000/ws/${projectId}`)
      
      websocket.onmessage = (event) => {
        const data = JSON.parse(event.data)
        setProjectStatus(data)
      }
      
      websocket.onerror = () => {
        console.error('WebSocket error')
      }
      
      setWs(websocket)
      
      return () => {
        websocket.close()
      }
    }
  }, [projectId, isGenerating])

  // Create new project
  const createProject = async () => {
    try {
      const response = await axios.post('/api/projects/create')
      setProjectId(response.data.project_id)
    } catch (error) {
      console.error('Failed to create project:', error)
    }
  }

  // Image dropzone
  const onDropImages = useCallback((acceptedFiles: File[]) => {
    setUploadedImages(prev => [...prev, ...acceptedFiles])
  }, [])

  const { getRootProps: getImageRootProps, getInputProps: getImageInputProps, isDragActive: isImageDragActive } = useDropzone({
    onDrop: onDropImages,
    accept: {
      'image/*': ['.jpg', '.jpeg', '.png', '.webp']
    },
    multiple: true
  })

  // Audio dropzone
  const onDropAudio = useCallback((acceptedFiles: File[]) => {
    if (acceptedFiles.length > 0) {
      setUploadedAudio(acceptedFiles[0])
    }
  }, [])

  const { getRootProps: getAudioRootProps, getInputProps: getAudioInputProps, isDragActive: isAudioDragActive } = useDropzone({
    onDrop: onDropAudio,
    accept: {
      'audio/*': ['.mp3', '.wav', '.ogg', '.m4a']
    },
    multiple: false
  })

  // Upload files to server
  const uploadFiles = async () => {
    if (!projectId) return

    try {
      // Upload images
      if (uploadedImages.length > 0) {
        const formData = new FormData()
        uploadedImages.forEach(file => {
          formData.append('files', file)
        })
        await axios.post(`/api/projects/${projectId}/upload/images`, formData)
      }

      // Upload audio
      if (uploadedAudio) {
        const formData = new FormData()
        formData.append('file', uploadedAudio)
        await axios.post(`/api/projects/${projectId}/upload/audio`, formData)
      }
    } catch (error) {
      console.error('Upload failed:', error)
    }
  }

  // Generate animation
  const handleGenerate = async () => {
    if (!projectId || uploadedImages.length === 0) {
      alert('Please upload at least one image')
      return
    }

    setIsGenerating(true)
    
    try {
      // Upload files first
      await uploadFiles()

      // Start generation
      const generationConfig = {
        ...config,
        project_id: projectId
      }

      await axios.post(`/api/projects/${projectId}/generate`, generationConfig)
    } catch (error) {
      console.error('Generation failed:', error)
      setIsGenerating(false)
    }
  }

  // Download video
  const handleDownload = async () => {
    if (!projectId || !projectStatus?.output_url) return

    try {
      const response = await axios.get(`/api/projects/${projectId}/download`, {
        responseType: 'blob'
      })
      
      const url = window.URL.createObjectURL(new Blob([response.data]))
      const link = document.createElement('a')
      link.href = url
      link.setAttribute('download', `animation_${projectId}.mp4`)
      document.body.appendChild(link)
      link.click()
      link.remove()
    } catch (error) {
      console.error('Download failed:', error)
    }
  }

  // Apply preset
  const applyPreset = (presetName: string) => {
    const preset = stylePresets.find(p => p.name === presetName)
    if (preset) {
      setSelectedPreset(presetName)
      setConfig(prev => ({
        ...prev,
        style_prompt: preset.prompt,
        ...preset.settings
      }))
    }
  }

  // Remove image
  const removeImage = (index: number) => {
    setUploadedImages(prev => prev.filter((_, i) => i !== index))
  }

  return (
    <>
      <Head>
        <title>AI Animation Platform</title>
        <meta name="description" content="Create audio-reactive animations with AI" />
        <meta name="viewport" content="width=device-width, initial-scale=1, maximum-scale=1, user-scalable=no" />
        <meta name="apple-mobile-web-app-capable" content="yes" />
        <meta name="apple-mobile-web-app-status-bar-style" content="black-translucent" />
      </Head>

      <div className="min-h-screen bg-gradient-to-br from-dark-900 via-dark-800 to-dark-900">
        {/* Header */}
        <header className="bg-dark-800/80 backdrop-blur-lg border-b border-dark-700 sticky top-0 z-50">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-3">
                <div className="w-10 h-10 bg-gradient-to-r from-primary-500 to-secondary-500 rounded-lg flex items-center justify-center">
                  <FiZap className="text-white text-xl" />
                </div>
                <h1 className="text-xl sm:text-2xl font-display font-bold text-white">
                  AI Animation
                </h1>
              </div>
              <button
                onClick={() => window.location.reload()}
                className="p-2 text-dark-400 hover:text-white transition-colors"
              >
                <FiRefreshCw className="text-xl" />
              </button>
            </div>
          </div>
        </header>

        <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6 sm:py-8">
          {/* Upload Section */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 sm:gap-6 mb-6">
            {/* Image Upload */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              className="bg-dark-800 rounded-xl p-4 sm:p-6 border border-dark-700"
            >
              <h2 className="text-lg font-semibold text-white mb-4 flex items-center">
                <FiImage className="mr-2" />
                Upload Images
                <span className="ml-auto text-sm text-dark-400">
                  {uploadedImages.length} files
                </span>
              </h2>
              
              <div
                {...getImageRootProps()}
                className={`border-2 border-dashed rounded-lg p-8 text-center cursor-pointer transition-all ${
                  isImageDragActive 
                    ? 'border-primary-500 bg-primary-500/10' 
                    : 'border-dark-600 hover:border-dark-500'
                }`}
              >
                <input {...getImageInputProps()} />
                <FiUpload className="mx-auto text-4xl text-dark-400 mb-3" />
                <p className="text-dark-300 mb-1">
                  {isImageDragActive ? 'Drop images here' : 'Drag & drop images'}
                </p>
                <p className="text-sm text-dark-500">or tap to browse</p>
              </div>

              {/* Image Preview */}
              {uploadedImages.length > 0 && (
                <div className="mt-4 grid grid-cols-3 gap-2">
                  {uploadedImages.map((file, index) => (
                    <div key={index} className="relative group">
                      <img
                        src={URL.createObjectURL(file)}
                        alt={`Upload ${index + 1}`}
                        className="w-full h-24 object-cover rounded-lg"
                      />
                      <button
                        onClick={() => removeImage(index)}
                        className="absolute top-1 right-1 p-1 bg-red-500 rounded-full opacity-0 group-hover:opacity-100 transition-opacity"
                      >
                        <FiX className="text-white text-sm" />
                      </button>
                    </div>
                  ))}
                </div>
              )}
            </motion.div>

            {/* Audio Upload */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.1 }}
              className="bg-dark-800 rounded-xl p-4 sm:p-6 border border-dark-700"
            >
              <h2 className="text-lg font-semibold text-white mb-4 flex items-center">
                <FiMusic className="mr-2" />
                Upload Audio (Optional)
              </h2>
              
              <div
                {...getAudioRootProps()}
                className={`border-2 border-dashed rounded-lg p-8 text-center cursor-pointer transition-all ${
                  isAudioDragActive 
                    ? 'border-secondary-500 bg-secondary-500/10' 
                    : 'border-dark-600 hover:border-dark-500'
                }`}
              >
                <input {...getAudioInputProps()} />
                <FiMusic className="mx-auto text-4xl text-dark-400 mb-3" />
                <p className="text-dark-300 mb-1">
                  {isAudioDragActive ? 'Drop audio here' : 'Drag & drop audio'}
                </p>
                <p className="text-sm text-dark-500">or tap to browse</p>
              </div>

              {uploadedAudio && (
                <div className="mt-4 p-3 bg-dark-700 rounded-lg flex items-center justify-between">
                  <div className="flex items-center space-x-3">
                    <FiMusic className="text-secondary-400" />
                    <span className="text-sm text-white truncate">
                      {uploadedAudio.name}
                    </span>
                  </div>
                  <button
                    onClick={() => setUploadedAudio(null)}
                    className="p-1 text-dark-400 hover:text-red-400"
                  >
                    <FiX />
                  </button>
                </div>
              )}
            </motion.div>
          </div>

          {/* Style Presets */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.2 }}
            className="bg-dark-800 rounded-xl p-4 sm:p-6 border border-dark-700 mb-6"
          >
            <h2 className="text-lg font-semibold text-white mb-4">Style Presets</h2>
            <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-3">
              {stylePresets.map((preset) => (
                <button
                  key={preset.name}
                  onClick={() => applyPreset(preset.name)}
                  className={`p-4 rounded-lg border-2 transition-all ${
                    selectedPreset === preset.name
                      ? 'border-primary-500 bg-primary-500/20'
                      : 'border-dark-600 hover:border-dark-500'
                  }`}
                >
                  <p className="text-sm font-medium text-white">{preset.name}</p>
                </button>
              ))}
            </div>
          </motion.div>

          {/* Configuration */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.3 }}
            className="bg-dark-800 rounded-xl p-4 sm:p-6 border border-dark-700 mb-6"
          >
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-lg font-semibold text-white flex items-center">
                <FiSettings className="mr-2" />
                Configuration
              </h2>
              <button
                onClick={() => setShowAdvanced(!showAdvanced)}
                className="text-sm text-primary-400 hover:text-primary-300"
              >
                {showAdvanced ? 'Hide' : 'Show'} Advanced
              </button>
            </div>

            {/* Basic Settings */}
            <div className="space-y-4">
              {/* Style Prompt */}
              <div>
                <label className="block text-sm font-medium text-dark-300 mb-2">
                  Style Prompt
                </label>
                <textarea
                  value={config.style_prompt}
                  onChange={(e) => setConfig({ ...config, style_prompt: e.target.value })}
                  className="w-full px-4 py-2 bg-dark-700 border border-dark-600 rounded-lg text-white placeholder-dark-400 focus:border-primary-500 focus:outline-none resize-none"
                  rows={2}
                  placeholder="Describe the visual style..."
                />
              </div>

              {/* Motion Intensity */}
              <div>
                <label className="block text-sm font-medium text-dark-300 mb-2">
                  Motion Intensity: {(config.motion_intensity! * 100).toFixed(0)}%
                </label>
                <input
                  type="range"
                  min="0"
                  max="1"
                  step="0.1"
                  value={config.motion_intensity}
                  onChange={(e) => setConfig({ ...config, motion_intensity: parseFloat(e.target.value) })}
                  className="w-full"
                />
              </div>

              {/* Grid Settings */}
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-dark-300 mb-2">
                    Zoom Effect
                  </label>
                  <select
                    value={config.zoom_effect}
                    onChange={(e) => setConfig({ ...config, zoom_effect: e.target.value })}
                    className="w-full px-4 py-2 bg-dark-700 border border-dark-600 rounded-lg text-white focus:border-primary-500 focus:outline-none"
                  >
                    <option value="none">None</option>
                    <option value="in">Zoom In</option>
                    <option value="out">Zoom Out</option>
                    <option value="pulse">Pulse</option>
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-dark-300 mb-2">
                    Rotation
                  </label>
                  <select
                    value={config.rotation}
                    onChange={(e) => setConfig({ ...config, rotation: e.target.value })}
                    className="w-full px-4 py-2 bg-dark-700 border border-dark-600 rounded-lg text-white focus:border-primary-500 focus:outline-none"
                  >
                    <option value="none">None</option>
                    <option value="cw">Clockwise</option>
                    <option value="ccw">Counter-clockwise</option>
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-dark-300 mb-2">
                    Color Grading
                  </label>
                  <select
                    value={config.color_grading}
                    onChange={(e) => setConfig({ ...config, color_grading: e.target.value })}
                    className="w-full px-4 py-2 bg-dark-700 border border-dark-600 rounded-lg text-white focus:border-primary-500 focus:outline-none"
                  >
                    <option value="neutral">Neutral</option>
                    <option value="warm">Warm</option>
                    <option value="cool">Cool</option>
                    <option value="vibrant">Vibrant</option>
                    <option value="muted">Muted</option>
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-dark-300 mb-2">
                    FPS
                  </label>
                  <select
                    value={config.fps}
                    onChange={(e) => setConfig({ ...config, fps: parseInt(e.target.value) })}
                    className="w-full px-4 py-2 bg-dark-700 border border-dark-600 rounded-lg text-white focus:border-primary-500 focus:outline-none"
                  >
                    <option value="24">24 FPS</option>
                    <option value="30">30 FPS</option>
                    <option value="60">60 FPS</option>
                  </select>
                </div>
              </div>
            </div>

            {/* Advanced Settings */}
            <AnimatePresence>
              {showAdvanced && (
                <motion.div
                  initial={{ height: 0, opacity: 0 }}
                  animate={{ height: 'auto', opacity: 1 }}
                  exit={{ height: 0, opacity: 0 }}
                  className="mt-6 pt-6 border-t border-dark-700 space-y-4"
                >
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <label className="block text-sm font-medium text-dark-300 mb-2">
                        Audio Reactivity
                      </label>
                      <select
                        value={config.audio_reactivity}
                        onChange={(e) => setConfig({ ...config, audio_reactivity: e.target.value })}
                        className="w-full px-4 py-2 bg-dark-700 border border-dark-600 rounded-lg text-white focus:border-primary-500 focus:outline-none"
                        disabled={!uploadedAudio}
                      >
                        <option value="off">Off</option>
                        <option value="low">Low</option>
                        <option value="medium">Medium</option>
                        <option value="high">High</option>
                      </select>
                    </div>

                    <div>
                      <label className="block text-sm font-medium text-dark-300 mb-2">
                        Frequency Focus
                      </label>
                      <select
                        value={config.audio_frequency}
                        onChange={(e) => setConfig({ ...config, audio_frequency: e.target.value })}
                        className="w-full px-4 py-2 bg-dark-700 border border-dark-600 rounded-lg text-white focus:border-primary-500 focus:outline-none"
                        disabled={!uploadedAudio || config.audio_reactivity === 'off'}
                      >
                        <option value="all">All</option>
                        <option value="low">Bass</option>
                        <option value="mid">Mids</option>
                        <option value="high">Treble</option>
                      </select>
                    </div>

                    <div>
                      <label className="block text-sm font-medium text-dark-300 mb-2">
                        Resolution
                      </label>
                      <select
                        value={config.resolution}
                        onChange={(e) => setConfig({ ...config, resolution: e.target.value })}
                        className="w-full px-4 py-2 bg-dark-700 border border-dark-600 rounded-lg text-white focus:border-primary-500 focus:outline-none"
                      >
                        <option value="720p">720p</option>
                        <option value="1080p">1080p</option>
                        <option value="4k">4K</option>
                      </select>
                    </div>

                    <div>
                      <label className="block text-sm font-medium text-dark-300 mb-2">
                        Quality
                      </label>
                      <select
                        value={config.quality_preset}
                        onChange={(e) => setConfig({ ...config, quality_preset: e.target.value })}
                        className="w-full px-4 py-2 bg-dark-700 border border-dark-600 rounded-lg text-white focus:border-primary-500 focus:outline-none"
                      >
                        <option value="fast">Fast</option>
                        <option value="balanced">Balanced</option>
                        <option value="quality">Quality</option>
                      </select>
                    </div>
                  </div>

                  {/* Effects Toggles */}
                  <div className="grid grid-cols-3 gap-4">
                    <label className="flex items-center space-x-2 cursor-pointer">
                      <input
                        type="checkbox"
                        checked={config.motion_blur}
                        onChange={(e) => setConfig({ ...config, motion_blur: e.target.checked })}
                        className="form-checkbox h-5 w-5 text-primary-500 rounded"
                      />
                      <span className="text-sm text-dark-300">Motion Blur</span>
                    </label>

                    <label className="flex items-center space-x-2 cursor-pointer">
                      <input
                        type="checkbox"
                        checked={config.depth_effect}
                        onChange={(e) => setConfig({ ...config, depth_effect: e.target.checked })}
                        className="form-checkbox h-5 w-5 text-primary-500 rounded"
                      />
                      <span className="text-sm text-dark-300">Depth Effect</span>
                    </label>

                    <label className="flex items-center space-x-2 cursor-pointer">
                      <input
                        type="checkbox"
                        checked={config.particle_effects}
                        onChange={(e) => setConfig({ ...config, particle_effects: e.target.checked })}
                        className="form-checkbox h-5 w-5 text-primary-500 rounded"
                      />
                      <span className="text-sm text-dark-300">Particles</span>
                    </label>
                  </div>
                </motion.div>
              )}
            </AnimatePresence>
          </motion.div>

          {/* Generate Button & Status */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.4 }}
            className="bg-dark-800 rounded-xl p-4 sm:p-6 border border-dark-700"
          >
            {!isGenerating ? (
              <button
                onClick={handleGenerate}
                disabled={uploadedImages.length === 0}
                className="w-full py-4 px-6 bg-gradient-to-r from-primary-500 to-secondary-500 text-white font-semibold rounded-lg hover:from-primary-600 hover:to-secondary-600 transition-all disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center space-x-3 text-lg"
              >
                <FiPlay />
                <span>Generate Animation</span>
              </button>
            ) : (
              <div className="space-y-4">
                {/* Progress Bar */}
                <div>
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-sm font-medium text-white">
                      {projectStatus?.message || 'Processing...'}
                    </span>
                    <span className="text-sm text-dark-400">
                      {projectStatus?.progress.toFixed(0)}%
                    </span>
                  </div>
                  <div className="w-full h-3 bg-dark-700 rounded-full overflow-hidden">
                    <motion.div
                      className="h-full bg-gradient-to-r from-primary-500 to-secondary-500"
                      initial={{ width: 0 }}
                      animate={{ width: `${projectStatus?.progress || 0}%` }}
                      transition={{ duration: 0.3 }}
                    />
                  </div>
                </div>

                {/* Status */}
                {projectStatus?.status === 'completed' && (
                  <button
                    onClick={handleDownload}
                    className="w-full py-4 px-6 bg-green-600 text-white font-semibold rounded-lg hover:bg-green-700 transition-all flex items-center justify-center space-x-3"
                  >
                    <FiDownload />
                    <span>Download Video</span>
                  </button>
                )}

                {projectStatus?.status === 'failed' && (
                  <div className="p-4 bg-red-500/20 border border-red-500 rounded-lg flex items-center space-x-3">
                    <FiAlertCircle className="text-red-400 text-xl" />
                    <p className="text-red-300">{projectStatus.message}</p>
                  </div>
                )}
              </div>
            )}
          </motion.div>
        </main>

        {/* Footer */}
        <footer className="mt-12 py-6 border-t border-dark-700">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
            <p className="text-dark-500 text-sm">
              AI Animation Platform • Audio-Reactive Video Generation
            </p>
          </div>
        </footer>
      </div>
    </>
  )
}
