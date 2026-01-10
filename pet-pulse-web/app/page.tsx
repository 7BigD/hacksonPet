'use client'
import { useState } from 'react'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';


export default function PetMagic() {
    const [file, setFile] = useState<File | null>(null);
    const [resultImg, setResultImg] = useState('');
    const [loading, setLoading] = useState(false);

    const handleUpload = async (mode: 'portrait' | 'meme') => {
        if (!file) return;
        setLoading(true);
        const formData = new FormData();
        formData.append('file', file);
        formData.append('mode', mode);

        const res = await fetch('${API_URL}/generate', {
            method: 'POST',
            body: formData,
        });
        const data = await res.json();
        setResultImg(`data:image/png;base64,${data.result}`);
        setLoading(false);
    };

    return (
        <div className="flex flex-col items-center p-10 bg-amber-50 min-h-screen">
            <h1 className="text-4xl font-bold mb-8 text-orange-600">🐾 PetPulse AI</h1>

            <input type="file" onChange={(e) => setFile(e.target.files?.[0] || null)} className="mb-4" />

            <div className="flex gap-4 mb-8">
                <button
                    onClick={() => handleUpload('portrait')}
                    className="bg-red-500 text-white px-6 py-2 rounded-full hover:bg-red-600 transition"
                    disabled={loading}
                >
                    🎅 生成圣诞写真
                </button>
                <button
                    onClick={() => handleUpload('meme')}
                    className="bg-yellow-500 text-white px-6 py-2 rounded-full hover:bg-yellow-600 transition"
                    disabled={loading}
                >
                    😂 制作灵魂表情包
                </button>
            </div>

            {loading && <div className="animate-bounce">🔮 正在施展魔法...</div>}

            {resultImg && (
                <div className="mt-4 border-8 border-white shadow-2xl rounded-lg overflow-hidden">
                    <img src={resultImg} alt="Result" className="max-w-md" />
                    <button className="w-full bg-green-500 text-white py-2">保存到相册</button>
                </div>
            )}
        </div>
    );
}