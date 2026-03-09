import React, { useEffect, useState } from 'react';
import { api } from '../services/api';
import { AlertCircle, ArrowRight, Phone, Smartphone, MapPin, Search, HelpCircle, MessageSquare, Activity, ExternalLink, ChevronRight, Hash } from 'lucide-react';

interface GapsPanelProps {
  startDate?: string;
  endDate?: string;
  onNavigateToThread?: (threadId: string) => void;
}

export const GapsPanel: React.FC<GapsPanelProps> = ({ startDate, endDate, onNavigateToThread }) => {
  const [data, setData] = useState<{
    gaps: Array<{
      macro: string;
      category: string;
      user_request: string;
      thread_ids: string[];
      count: number;
    }>;
    top_themes: Array<{
      macro: string;
      category: string;
      count: number;
      examples: string[];
    }>;
    referrals: {
      distribution: Array<{
        channel: string;
        count: number;
        percentage: number;
      }>;
      total_referrals: number;
      total_conversations: number;
    };
  } | null>(null);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [viewMode, setViewMode] = useState<'themes' | 'table'>('themes');
  const [expandedThreads, setExpandedThreads] = useState<Record<string, boolean>>({});

  useEffect(() => {
    const fetchGaps = async () => {
      setLoading(true);
      try {
        const res = await api.getGaps({ start_date: startDate, end_date: endDate });
        setData(res);
      } catch (error) {
        console.error("Error fetching gaps data:", error);
      } finally {
        setLoading(false);
      }
    };
    fetchGaps();
  }, [startDate, endDate]);

  const filteredGaps = data?.gaps.filter(g => 
    g.user_request.toLowerCase().includes(searchTerm.toLowerCase()) ||
    g.category.toLowerCase().includes(searchTerm.toLowerCase())
  ) || [];

  if (loading) return (
    <div className="flex flex-col items-center justify-center p-12 text-gray-500">
      <div className="animate-spin rounded-full h-10 w-10 border-b-2 border-blue-600 mb-4"></div>
      Analizando vacíos de conocimiento y redirecciones...
    </div>
  );

  const getChannelIcon = (channel: string) => {
    if (channel.includes('Telefónico')) return <Phone className="text-blue-500" size={20} />;
    if (channel.includes('Digital')) return <Smartphone className="text-emerald-500" size={20} />;
    if (channel.includes('Físico')) return <MapPin className="text-orange-500" size={20} />;
    return <ArrowRight className="text-gray-400" size={20} />;
  };

  const toggleThreads = (requestId: string) => {
    setExpandedThreads(prev => ({
      ...prev,
      [requestId]: !prev[requestId]
    }));
  };

  return (
    <div className="space-y-8 animate-in fade-in duration-500">
      {/* Resumen de Canales */}
      <div className="bg-white p-6 rounded-2xl border border-gray-200 shadow-sm overflow-hidden">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 mb-6">
            <h3 className="text-lg font-bold text-gray-900 flex items-center gap-2">
                <Activity className="text-indigo-600" />
                Distribución de Redirecciones por Canal
            </h3>
            <div className="px-4 py-1.5 bg-indigo-50 border border-indigo-100 rounded-full">
                <p className="text-[10px] font-bold text-indigo-600 uppercase tracking-wider text-center">
                    Cálculo basado en el 100% de Conversaciones ({data?.referrals.total_conversations.toLocaleString()})
                </p>
            </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            {data?.referrals.distribution.map((item, idx) => (
                <div key={idx} className="p-4 bg-gray-50 border border-gray-100 rounded-xl relative overflow-hidden group hover:border-blue-200 transition-all">
                    <div className="flex items-center gap-3 mb-3">
                        <div className="p-2 bg-white rounded-lg shadow-sm">
                            {getChannelIcon(item.channel)}
                        </div>
                        <div className="text-xs font-bold text-gray-400 uppercase tracking-tighter">{item.channel}</div>
                    </div>
                    <div className="flex items-baseline gap-1">
                        <span className="text-2xl font-black text-gray-900">{item.percentage}%</span>
                        <span className="text-[10px] text-gray-400 font-bold uppercase">({item.count} convs)</span>
                    </div>
                    <div className="w-full h-1.5 bg-gray-200 rounded-full mt-3 overflow-hidden">
                        <div 
                            className={`h-full transition-all duration-1000 ${
                                item.channel.includes('Telefónico') ? 'bg-blue-500' : 
                                item.channel.includes('Digital') ? 'bg-emerald-500' : 
                                'bg-orange-500'
                            }`} 
                            style={{ width: `${item.percentage}%` }}
                        ></div>
                    </div>
                </div>
            ))}
            <div className="p-4 bg-indigo-600 rounded-xl text-white shadow-lg flex flex-col justify-center">
                 <div className="text-[10px] font-bold uppercase tracking-widest opacity-70">Total Referidas</div>
                 <div className="text-3xl font-black">{data?.referrals.total_referrals.toLocaleString()}</div>
                 <div className="text-[10px] opacity-60 font-medium">Conversaciones únicas</div>
            </div>
        </div>
      </div>

      {/* Panel de Gaps */}
      <div className="bg-white p-6 rounded-2xl border border-gray-200 shadow-sm relative">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-6 mb-8">
            <div className="flex items-center gap-4">
                <div className="p-3 bg-rose-50 rounded-xl">
                    <AlertCircle className="text-rose-600" size={24} />
                </div>
                <div>
                   <h3 className="text-xl font-black text-gray-900 leading-none mb-1">Vacíos de Conocimiento (AI Gaps)</h3>
                   <p className="text-sm text-gray-500 font-medium">Temas frecuentes que la IA no pudo resolver.</p>
                </div>
            </div>

            <div className="flex flex-wrap items-center gap-4">
                <div className="flex bg-gray-100 p-1 rounded-lg">
                    <button 
                        onClick={() => setViewMode('themes')}
                        className={`px-4 py-1.5 text-xs font-bold rounded-md transition-all ${viewMode === 'themes' ? 'bg-white text-gray-900 shadow-sm' : 'text-gray-500 hover:text-gray-700'}`}
                    >
                        Temas (Mosaico)
                    </button>
                    <button 
                        onClick={() => setViewMode('table')}
                        className={`px-4 py-1.5 text-xs font-bold rounded-md transition-all ${viewMode === 'table' ? 'bg-white text-gray-900 shadow-sm' : 'text-gray-500 hover:text-gray-700'}`}
                    >
                        Ejemplos (Lista)
                    </button>
                </div>

                <div className="relative">
                   <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" size={14} />
                   <input 
                       type="text"
                       placeholder="Filtrar por tema..."
                       className="pl-10 pr-4 py-2 bg-gray-50 border border-gray-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 w-full md:w-56"
                       value={searchTerm}
                       onChange={(e) => setSearchTerm(e.target.value)}
                   />
                </div>
            </div>
        </div>

        {viewMode === 'themes' ? (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                {data?.top_themes.filter(t => t.category.toLowerCase().includes(searchTerm.toLowerCase())).map((theme, i) => (
                    <div key={i} className="flex flex-col bg-white border border-gray-100 rounded-2xl p-5 hover:border-blue-200 hover:shadow-lg transition-all group overflow-hidden relative">
                        <div className="absolute top-0 right-0 p-4 opacity-5 group-hover:opacity-10 group-hover:scale-110 transition-all">
                             <HelpCircle size={60} />
                        </div>
                        
                        <div className="flex items-center justify-between mb-4">
                            <div className="px-2.5 py-1 bg-gray-100 rounded-lg text-[10px] font-black text-gray-500 uppercase tracking-wider">{theme.macro}</div>
                            <div className="flex items-center gap-1.5 px-2.5 py-1 bg-rose-50 text-rose-700 rounded-lg text-xs font-black border border-rose-100">
                                <AlertCircle size={12} /> {theme.count}
                            </div>
                        </div>
                        
                        <h4 className="text-lg font-black text-gray-900 mb-4 line-clamp-1 group-hover:text-blue-600 transition-colors">{theme.category}</h4>
                        
                        <div className="space-y-3 flex-1 mb-6">
                            {theme.examples.map((ex, idx) => (
                                <div key={idx} className="flex items-start gap-2 text-xs font-medium text-gray-500 italic bg-gray-50/50 p-2 rounded-lg border border-gray-100/50 group-hover:bg-white transition-colors">
                                    <MessageSquare size={12} className="text-blue-400 mt-0.5 shrink-0" />
                                    <span className="line-clamp-2 leading-relaxed">"{ex}"</span>
                                </div>
                            ))}
                        </div>

                        <button 
                            onClick={() => {
                                setSearchTerm(theme.category);
                                setViewMode('table');
                            }}
                            className="w-full flex items-center justify-center gap-2 py-2.5 bg-gray-50 text-gray-600 rounded-xl text-xs font-bold hover:bg-blue-600 hover:text-white transition-all transform active:scale-95"
                        >
                            Ver todos los hilos <ChevronRight size={14} />
                        </button>
                    </div>
                ))}
            </div>
        ) : (
            <div className="overflow-x-auto rounded-xl border border-gray-100 shadow-inner bg-gray-50/20">
                <table className="w-full text-sm text-left text-gray-500">
                    <thead className="text-[10px] text-gray-400 uppercase bg-gray-50/50">
                        <tr>
                            <th className="px-6 py-4 font-black">Macro / Categoría</th>
                            <th className="px-6 py-4 font-black">Lo que el usuario solicitó</th>
                            <th className="px-6 py-4 text-center font-black">Incidencias</th>
                            <th className="px-6 py-4 text-center font-black w-48">Hilos Relacionados</th>
                        </tr>
                    </thead>
                    <tbody className="divide-y divide-gray-100 bg-white">
                        {filteredGaps.map((gap, i) => {
                            const requestId = `${gap.category}-${i}`;
                            const isExpanded = expandedThreads[requestId];
                            
                            return (
                                <React.Fragment key={requestId}>
                                    <tr className="hover:bg-blue-50/30 transition-colors group">
                                        <td className="px-6 py-4 whitespace-nowrap">
                                            <div className="flex flex-col">
                                                <span className="text-[9px] text-gray-400 font-bold uppercase mb-1">{gap.macro}</span>
                                                <span className="font-bold text-gray-800">{gap.category}</span>
                                            </div>
                                        </td>
                                        <td className="px-6 py-4">
                                            <div className="flex items-start gap-3">
                                                <div className="p-1.5 bg-blue-50 rounded text-blue-400 shrink-0">
                                                    <MessageSquare size={14} />
                                                </div>
                                                <span className="text-gray-700 italic leading-snug">"{gap.user_request}"</span>
                                            </div>
                                        </td>
                                        <td className="px-6 py-4 text-center">
                                            <span className="inline-flex items-center justify-center h-8 min-w-[32px] px-2 bg-rose-50 text-rose-700 text-xs font-black rounded-lg border border-rose-100">
                                                {gap.count}
                                            </span>
                                        </td>
                                        <td className="px-6 py-4 text-center">
                                            <button 
                                                onClick={() => toggleThreads(requestId)}
                                                className={`inline-flex items-center gap-2 px-3 py-2 rounded-lg text-xs font-bold transition-all active:scale-95 ${
                                                    isExpanded 
                                                    ? 'bg-gray-100 text-gray-800' 
                                                    : 'bg-indigo-600 text-white shadow-sm hover:bg-indigo-700'
                                                }`}
                                            >
                                                {isExpanded ? 'Ocultar' : 'Ver todos'} ({gap.thread_ids.length})
                                            </button>
                                        </td>
                                    </tr>
                                    {isExpanded && (
                                        <tr className="bg-gray-50/50">
                                            <td colSpan={4} className="px-12 py-6">
                                                <div className="flex flex-wrap gap-2">
                                                    {gap.thread_ids.map((tid, tIdx) => (
                                                        <button 
                                                            key={tIdx}
                                                            onClick={() => onNavigateToThread?.(tid)}
                                                            className="flex items-center gap-2 px-4 py-2 bg-white border border-indigo-100 rounded-xl text-xs font-bold text-indigo-600 hover:bg-indigo-600 hover:text-white transition-all group/tid shadow-sm"
                                                        >
                                                            <Hash size={12} className="opacity-50" />
                                                            {tid}
                                                            <ExternalLink size={10} className="ml-1 opacity-0 group-hover/tid:opacity-100 transition-opacity" />
                                                        </button>
                                                    ))}
                                                </div>
                                            </td>
                                        </tr>
                                    )}
                                </React.Fragment>
                            );
                        })}
                    </tbody>
                </table>
            </div>
        )}
      </div>

      <div className="bg-gradient-to-br from-indigo-700 to-blue-800 rounded-3xl p-8 text-white shadow-2xl relative overflow-hidden">
        <div className="absolute top-0 right-0 -m-12 opacity-10">
           <Activity size={300} />
        </div>
        <div className="relative z-10 flex flex-col md:flex-row items-center gap-8">
           <div className="p-5 bg-white/10 rounded-2xl backdrop-blur-md shadow-xl border border-white/20">
              <TrendingUp size={48} />
           </div>
           <div>
              <h4 className="text-2xl font-black mb-2 tracking-tight">Estrategia de Optimización</h4>
              <p className="text-white/80 text-lg max-w-2xl leading-relaxed">
                Has identificado <span className="text-yellow-400 font-bold">{data?.gaps.length}</span> motivos únicos de fallo. 
                El <span className="font-black text-white italic">"{data?.referrals.distribution.find(d => d.channel.includes('Telefónico'))?.percentage}%"</span> de tus conversaciones terminan redigiridas a Servilínea por falta de información directa.
              </p>
           </div>
           <div className="flex-1 text-right">
                <button 
                  onClick={() => setViewMode('themes')}
                  className="px-6 py-3 bg-white text-blue-700 rounded-2xl font-black text-sm hover:bg-blue-50 transition-colors shadow-lg"
                >
                    Filtros por Prioridad
                </button>
           </div>
        </div>
      </div>
    </div>
  );
};

const TrendingUp = ({ size }: { size: number }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <polyline points="23 6 13.5 15.5 8.5 10.5 1 18"></polyline>
    <polyline points="17 6 23 6 23 12"></polyline>
  </svg>
);
