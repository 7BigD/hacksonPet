'use client'
import { useState, useRef } from 'react'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

// Allowed image formats
const ALLOWED_TYPES = ['image/jpeg', 'image/png', 'image/webp'];
const MAX_FILE_SIZE = 10 * 1024 * 1024; // 10MB

interface ImageUploadProps {
    label: string;
    description: string;
    file: File | null;
    preview: string;
    onFileChange: (file: File | null, preview: string) => void;
}

function ImageUpload({ label, description, file, preview, onFileChange }: ImageUploadProps) {
    const inputRef = useRef<HTMLInputElement>(null);

    const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
        const selectedFile = e.target.files?.[0];
        if (!selectedFile) return;

        // Validate file type
        if (!ALLOWED_TYPES.includes(selectedFile.type)) {
            alert('Unsupported format. Please upload JPG, PNG, or WebP image.');
            return;
        }

        // Validate file size
        if (selectedFile.size > MAX_FILE_SIZE) {
            alert('File size exceeds 10MB limit.');
            return;
        }

        // Create preview URL
        const previewUrl = URL.createObjectURL(selectedFile);
        onFileChange(selectedFile, previewUrl);
    };

    const handleRemove = () => {
        if (preview) {
            URL.revokeObjectURL(preview);
        }
        onFileChange(null, '');
        if (inputRef.current) {
            inputRef.current.value = '';
        }
    };

    const handleClick = () => {
        inputRef.current?.click();
    };

    return (
        <div className="flex flex-col items-center">
            <h3 className="text-lg font-semibold text-gray-700 mb-2">{label}</h3>
            <p className="text-sm text-gray-500 mb-3">{description}</p>

            <input
                ref={inputRef}
                type="file"
                accept="image/jpeg,image/png,image/webp"
                onChange={handleFileSelect}
                className="hidden"
            />

            {!preview ? (
                <div
                    onClick={handleClick}
                    className="w-64 h-64 border-2 border-dashed border-gray-300 rounded-xl flex flex-col items-center justify-center cursor-pointer hover:border-purple-500 hover:bg-purple-50 transition-all"
                >
                    <svg className="w-12 h-12 text-gray-400 mb-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
                    </svg>
                    <span className="text-gray-500">Click to upload</span>
                    <span className="text-xs text-gray-400 mt-1">JPG, PNG, WebP (max 10MB)</span>
                </div>
            ) : (
                <div className="relative group">
                    <img
                        src={preview}
                        alt={label}
                        className="w-64 h-64 object-cover rounded-xl border-2 border-purple-300 shadow-lg"
                    />
                    <div className="absolute inset-0 bg-black bg-opacity-40 opacity-0 group-hover:opacity-100 transition-opacity rounded-xl flex items-center justify-center gap-2">
                        <button
                            onClick={handleClick}
                            className="bg-white text-gray-700 px-3 py-1 rounded-lg text-sm hover:bg-gray-100"
                        >
                            Replace
                        </button>
                        <button
                            onClick={handleRemove}
                            className="bg-red-500 text-white px-3 py-1 rounded-lg text-sm hover:bg-red-600"
                        >
                            Remove
                        </button>
                    </div>
                    <div className="mt-2 text-center">
                        <span className="text-sm text-gray-600 truncate block max-w-[250px]">{file?.name}</span>
                    </div>
                </div>
            )}
        </div>
    );
}

export default function HumanPortrait() {
    const [mainFile, setMainFile] = useState<File | null>(null);
    const [mainPreview, setMainPreview] = useState('');
    const [styleFile, setStyleFile] = useState<File | null>(null);
    const [stylePreview, setStylePreview] = useState('');
    const [resultImg, setResultImg] = useState('');
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState('');

    const handleMainFileChange = (file: File | null, preview: string) => {
        setMainFile(file);
        setMainPreview(preview);
        setError('');
    };

    const handleStyleFileChange = (file: File | null, preview: string) => {
        setStyleFile(file);
        setStylePreview(preview);
        setError('');
    };

    const handleGenerate = async () => {
        // Validate both images are uploaded
        if (!mainFile) {
            setError('Please upload your photo first.');
            return;
        }
        if (!styleFile) {
            setError('Please upload a style reference image.');
            return;
        }

        setLoading(true);
        setError('');
        setResultImg('');

        try {
            const formData = new FormData();
            formData.append('main_file', mainFile);
            formData.append('style_file', styleFile);

            console.log("Requesting:", `${API_URL}/generate`);

            const controller = new AbortController();
            const timeoutId = setTimeout(() => controller.abort(), 60000); // 60s timeout

            const res = await fetch(`${API_URL}/generate`, {
                method: 'POST',
                body: formData,
                signal: controller.signal,
            });

            clearTimeout(timeoutId);

            if (!res.ok) {
                const errorData = await res.json().catch(() => ({}));
                throw new Error(errorData.detail || `Request failed: ${res.status}`);
            }

            const data = await res.json();
            setResultImg(`data:image/png;base64,${data.result}`);
        } catch (err) {
            if (err instanceof Error) {
                if (err.name === 'AbortError') {
                    setError('Request timeout. Please try again.');
                } else {
                    setError(err.message);
                }
            } else {
                setError('Generation failed. Please try again.');
            }
        } finally {
            setLoading(false);
        }
    };

    const handleDownload = () => {
        if (!resultImg) return;

        const link = document.createElement('a');
        link.href = resultImg;
        link.download = `portrait_${Date.now()}.png`;
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
    };

    const handleRegenerate = () => {
        setResultImg('');
        handleGenerate();
    };

    const handleReset = () => {
        // Clean up preview URLs
        if (mainPreview) URL.revokeObjectURL(mainPreview);
        if (stylePreview) URL.revokeObjectURL(stylePreview);

        setMainFile(null);
        setMainPreview('');
        setStyleFile(null);
        setStylePreview('');
        setResultImg('');
        setError('');
    };

    return (
        <div className="flex flex-col items-center p-10 bg-gradient-to-br from-purple-50 to-pink-50 min-h-screen">
            <h1 className="text-4xl font-bold mb-2 bg-gradient-to-r from-purple-600 to-pink-600 bg-clip-text text-transparent">
                ✨ AI Portrait Studio
            </h1>
            <p className="text-gray-600 mb-8">Transform your photos into stunning portraits</p>

            {/* Upload Section */}
            <div className="flex flex-col md:flex-row gap-8 mb-8">
                <ImageUpload
                    label="📷 Your Photo"
                    description="Upload the photo to transform"
                    file={mainFile}
                    preview={mainPreview}
                    onFileChange={handleMainFileChange}
                />
                <ImageUpload
                    label="🎨 Style Reference"
                    description="Upload a style reference image"
                    file={styleFile}
                    preview={stylePreview}
                    onFileChange={handleStyleFileChange}
                />
            </div>

            {/* Error Message */}
            {error && (
                <div className="mb-4 px-4 py-2 bg-red-100 border border-red-300 text-red-700 rounded-lg">
                    {error}
                </div>
            )}

            {/* Action Buttons */}
            <div className="flex gap-4 mb-8">
                <button
                    onClick={handleGenerate}
                    disabled={loading || !mainFile || !styleFile}
                    className={`px-8 py-3 rounded-full font-semibold text-white transition-all transform hover:scale-105 ${loading || !mainFile || !styleFile
                            ? 'bg-gray-400 cursor-not-allowed'
                            : 'bg-gradient-to-r from-purple-600 to-pink-600 hover:from-purple-700 hover:to-pink-700 shadow-lg'
                        }`}
                >
                    {loading ? '✨ Generating...' : '🚀 Generate Portrait'}
                </button>
                {(mainFile || styleFile) && !loading && (
                    <button
                        onClick={handleReset}
                        className="px-6 py-3 rounded-full font-semibold text-gray-600 bg-white border border-gray-300 hover:bg-gray-50 transition-all"
                    >
                        🔄 Reset
                    </button>
                )}
            </div>

            {/* Loading State */}
            {loading && (
                <div className="flex flex-col items-center mb-8">
                    <div className="w-16 h-16 border-4 border-purple-200 border-t-purple-600 rounded-full animate-spin mb-4"></div>
                    <p className="text-purple-600 font-medium">Creating your portrait...</p>
                    <p className="text-sm text-gray-500">This may take up to 30 seconds</p>
                </div>
            )}

            {/* Result Section */}
            {resultImg && (
                <div className="flex flex-col items-center animate-fade-in">
                    <h2 className="text-2xl font-bold text-gray-700 mb-4">🎉 Your Portrait is Ready!</h2>
                    <div className="relative border-4 border-white shadow-2xl rounded-2xl overflow-hidden mb-4">
                        <img src={resultImg} alt="Generated Portrait" className="max-w-md" />
                    </div>
                    <div className="flex gap-4">
                        <button
                            onClick={handleDownload}
                            className="px-6 py-2 bg-green-500 text-white rounded-full font-semibold hover:bg-green-600 transition-all flex items-center gap-2"
                        >
                            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
                            </svg>
                            Download
                        </button>
                        <button
                            onClick={handleRegenerate}
                            disabled={loading}
                            className="px-6 py-2 bg-purple-500 text-white rounded-full font-semibold hover:bg-purple-600 transition-all flex items-center gap-2"
                        >
                            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                            </svg>
                            Regenerate
                        </button>
                    </div>
                </div>
            )}
        </div>
    );
}