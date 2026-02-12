
import { useEffect, useState } from 'react';
import { api } from '../services/api';

export const WordCloud = () => {
    const [image, setImage] = useState<string | null>(null);
    const [loading, setLoading] = useState(true);
    const [intencion, setIntencion] = useState('');
    const [options, setOptions] = useState<string[]>([]);

    useEffect(() => {
         api.getOptions().then(res => setOptions(res.intenciones));
    }, []);

    useEffect(() => {
        setLoading(true);
        api.getWordCloud(intencion || undefined).then(res => {
            setImage(res.image);
        }).finally(() => setLoading(false));
    }, [intencion]);

    return (
        <div className="bg-white rounded-lg shadow-sm border border-gray-100 p-6 flex flex-col h-full">
            <div className="mb-6 flex justify-between items-center">
                <h3 className="text-lg font-semibold text-gray-800">Nube de Palabras</h3>
                <select 
                    className="px-3 py-2 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                    value={intencion}
                    onChange={(e) => setIntencion(e.target.value)}
                >
                    <option value="">Todas las intenciones</option>
                    {options.map(opt => <option key={opt} value={opt}>{opt}</option>)}
                </select>
            </div>
            
            <div className="flex-1 flex items-center justify-center bg-gray-50 rounded-lg overflow-hidden border border-gray-100 min-h-[400px]">
                {loading ? (
                    <div className="text-gray-400 animate-pulse">Generando nube de palabras...</div>
                ) : image ? (
                    <img src={`data:image/png;base64,${image}`} alt="Word Cloud" className="max-w-full h-auto" />
                ) : (
                    <div className="text-gray-400">No hay datos suficientes para generar la nube.</div>
                )}
            </div>
        </div>
    );
};
