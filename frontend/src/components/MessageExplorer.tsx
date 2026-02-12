import React, { useState, useEffect } from 'react';
import { api } from '../services/api';
import { Search, ChevronLeft, ChevronRight, PhoneCall } from 'lucide-react';


interface MessageExplorerProps {
    initialThreadId?: string;
    startDate?: string;
    endDate?: string;
}

export const MessageExplorer = ({ initialThreadId, startDate, endDate }: MessageExplorerProps) => {
    const [messages, setMessages] = useState<any[]>([]);
    const [total, setTotal] = useState(0);
    const [page, setPage] = useState(1);
    const [loading, setLoading] = useState(false);
    const [options, setOptions] = useState<any>({ intenciones: [], productos: [], sentimientos: [] });
    
    // Filters
    const [search, setSearch] = useState('');
    const [intencion, setIntencion] = useState('');
    const [sentiment, setSentiment] = useState('');
    const [product, setProduct] = useState('');
    const [senderType, setSenderType] = useState(''); // 'human' | 'ai'
    const [threadId, setThreadId] = useState(initialThreadId || '');
    const [excludeEmpty, setExcludeEmpty] = useState(false);
    const [sortBy, setSortBy] = useState(''); // '' | 'length_asc' | 'length_desc'

    const [debouncedSearch, setDebouncedSearch] = useState(search);

    useEffect(() => {
        api.getOptions().then(setOptions).catch(console.error);
    }, []);

    // Update threadId if prop changes
    useEffect(() => {
        if (initialThreadId) {
            setThreadId(initialThreadId);
            setSenderType(''); 
            setPage(1);
        }
    }, [initialThreadId]);

    // Debounce search effect
    useEffect(() => {
        const timer = setTimeout(() => {
            setDebouncedSearch(search);
        }, 500);
        return () => clearTimeout(timer);
    }, [search]);

    // Reset page when filters change (except page itself)
    useEffect(() => {
        setPage(1);
    }, [debouncedSearch, intencion, sentiment, product, senderType, threadId, excludeEmpty, sortBy, startDate, endDate]);

    const fetchMessages = React.useCallback(async () => {
        setLoading(true);
        try {
            const res = await api.getMessages({
                page,
                limit: 20,
                search: debouncedSearch || undefined,
                intencion: intencion || undefined,
                sentiment: sentiment || undefined,
                product: product || undefined,
                sender_type: senderType || undefined,
                thread_id: threadId || undefined,
                exclude_empty: excludeEmpty,
                sort_by: sortBy || undefined,
                start_date: startDate,
                end_date: endDate
            });
            setMessages(res.data);
            setTotal(res.total);
        } catch (error) {
            console.error(error);
        } finally {
            setLoading(false);
        }
    }, [page, debouncedSearch, intencion, sentiment, product, senderType, threadId, excludeEmpty, sortBy, startDate, endDate]);

    useEffect(() => {
        fetchMessages();
    }, [fetchMessages]); 

    
    // Let's go with `debouncedSearch` pattern for cleanliness
    // But to respect existing structure without massive refactor:
    // We already have `fetchMessages` dependent on `search`.
    // We should NOT include `search` in `fetchMessages` dependency array if we want to debounce it manually here.
    // However, simplest fix for "not loading" is usually that it WAS loading but effect dependencies were wrong.
    // The previous code had empty body in debounce effect! 
    
    // The logic below ensures that when `search` changes, we wait 500ms then trigger the fetch depending on whether page needs reset.


    const totalPages = Math.ceil(total / 20);

    return (
        <div className="bg-white rounded-lg shadow-sm border border-gray-100 flex flex-col h-full">
            {/* Filters Header */}
            <div className="p-4 border-b border-gray-100 space-y-4">
                <div className="flex gap-4">
                    <div className="relative flex-1">
                        <Search className="absolute left-3 top-2.5 text-gray-400 w-5 h-5" />
                        <input 
                            type="text" 
                            placeholder="Buscar en mensajes..." 
                            className="w-full pl-10 pr-4 py-2 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                            value={search}
                            onChange={(e) => setSearch(e.target.value)}
                        />
                    </div>
                </div>
                
                <div className="flex gap-4 flex-wrap items-center">
                    {/* Thread Filter Active Indicator */}
                    {threadId && (
                        <div className="flex items-center gap-2 bg-blue-50 px-3 py-2 rounded-lg border border-blue-200">
                            <span className="text-sm text-blue-800 font-medium">Hilo: {threadId.substring(0, 8)}...</span>
                            <button 
                                onClick={() => { setThreadId(''); setPage(1); }}
                                className="text-blue-500 hover:text-blue-700"
                                title="Ver todos los mensajes"
                            >
                                ✕
                            </button>
                        </div>
                    )}

                    <select 
                        className="px-3 py-2 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                        value={senderType}
                        onChange={(e) => { setSenderType(e.target.value); setPage(1); }}
                    >
                        <option value="">Todos los remitentes</option>
                        <option value="human">Humano</option>
                        <option value="ai">IA</option>
                    </select>

                    <select 
                        className="px-3 py-2 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                        value={intencion}
                        onChange={(e) => { setIntencion(e.target.value); setPage(1); }}
                    >
                        <option value="">Todas las intenciones</option>
                        {options.intenciones.map((i: string) => <option key={i} value={i}>{i}</option>)}
                    </select>
                    
                    <select 
                        className="px-3 py-2 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                        value={sortBy}
                        onChange={(e) => { setSortBy(e.target.value); setPage(1); }}
                    >
                        <option value="">Ordenar por...</option>
                        <option value="length_desc">Más largas primero</option>
                        <option value="length_asc">Más cortas primero</option>
                    </select>

                    <select 
                        className="px-3 py-2 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                        value={sentiment}
                        onChange={(e) => { setSentiment(e.target.value); setPage(1); }}
                    >
                        <option value="">Cualquier sentimiento</option>
                        {options.sentimientos.map((s: string) => <option key={s} value={s}>{s}</option>)}
                    </select>

                     <select 
                        className="px-3 py-2 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                        value={product}
                        onChange={(e) => { setProduct(e.target.value); setPage(1); }}
                    >
                        <option value="">Todos los productos</option>
                        {options.productos.map((p: string) => <option key={p} value={p}>{p}</option>)}
                    </select>

                   <label className="flex items-center gap-2 text-sm text-gray-700 select-none cursor-pointer">
                      <input 
                        type="checkbox" 
                        checked={excludeEmpty}
                        onChange={(e) => { setExcludeEmpty(e.target.checked); setPage(1); }}
                        className="rounded text-blue-600 focus:ring-blue-500 border-gray-300"
                      />
                      Excluir vacíos
                   </label>
                </div>
            </div>

            {/* Table */}
            <div className="flex-1 overflow-auto">
                <table className="w-full text-left border-collapse">
                    <thead className="bg-gray-50 sticky top-0 z-10 shadow-sm">
                        <tr>
                            <th className="px-6 py-3 text-xs font-medium text-gray-500 uppercase tracking-wider bg-gray-50 border-b border-gray-200">Fecha</th>
                            <th className="px-6 py-3 text-xs font-medium text-gray-500 uppercase tracking-wider bg-gray-50 border-b border-gray-200">Thread ID</th>
                            <th className="px-6 py-3 text-xs font-medium text-gray-500 uppercase tracking-wider bg-gray-50 border-b border-gray-200">Remitente</th>
                            <th className="px-6 py-3 text-xs font-medium text-gray-500 uppercase tracking-wider bg-gray-50 border-b border-gray-200">Mensaje</th>
                            <th className="px-6 py-3 text-xs font-medium text-gray-500 uppercase tracking-wider bg-gray-50 border-b border-gray-200">Intención</th>
                            <th className="px-6 py-3 text-xs font-medium text-gray-500 uppercase tracking-wider bg-gray-50 border-b border-gray-200">Sentimiento</th>
                            <th className="px-6 py-3 text-xs font-medium text-gray-500 uppercase tracking-wider bg-gray-50 border-b border-gray-200 text-center">Servilínea</th>
                            <th className="px-6 py-3 text-xs font-medium text-gray-500 uppercase tracking-wider bg-gray-50 border-b border-gray-200 text-right">Acciones</th>
                        </tr>
                    </thead>
                    <tbody className="divide-y divide-gray-100">
                        {loading ? (
                            Array.from({ length: 5 }).map((_, i) => (
                                <tr key={i} className="animate-pulse">
                                    <td className="px-6 py-4"><div className="h-4 bg-gray-200 rounded w-24"></div></td>
                                    <td className="px-6 py-4"><div className="h-4 bg-gray-200 rounded w-16"></div></td>
                                    <td className="px-6 py-4"><div className="h-4 bg-gray-200 rounded w-64"></div></td>
                                    <td className="px-6 py-4"><div className="h-4 bg-gray-200 rounded w-32"></div></td>
                                    <td className="px-6 py-4"><div className="h-4 bg-gray-200 rounded w-16"></div></td>
                                    <td className="px-6 py-4"><div className="h-4 bg-gray-200 rounded w-16"></div></td>
                                    <td className="px-6 py-4"><div className="h-4 bg-gray-200 rounded w-16"></div></td>
                                    <td className="px-6 py-4"><div className="h-4 bg-gray-200 rounded w-16"></div></td>
                                </tr>
                            ))
                        ) : (
                            messages.map((msg, idx) => (
                                <tr key={idx} className="hover:bg-gray-50">
                                    <td className="px-6 py-4 text-sm text-gray-500 whitespace-nowrap">
                                        {msg.fecha} {msg.hora}:00
                                        {msg.thread_length > 0 && (
                                            <div className="text-xs text-gray-400 mt-1">
                                                Hilo de {msg.thread_length} msjs
                                            </div>
                                        )}
                                    </td>
                                    <td className="px-6 py-4 text-sm font-mono text-gray-400 text-xs select-all">
                                        {msg.thread_id}
                                    </td>
                                    <td className="px-6 py-4 text-sm">
                                        <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                                            msg.type === 'human' ? 'bg-blue-100 text-blue-800' : 'bg-purple-100 text-purple-800'
                                        }`}>
                                            {msg.type === 'human' ? 'Usuario' : 'IA'}
                                        </span>
                                    </td>
                                    <td className="px-6 py-4 text-sm text-gray-900 max-w-md truncate" title={msg.text}>
                                        {msg.text || <span className="text-gray-300 italic">(vacío)</span>}
                                    </td>
                                    <td className="px-6 py-4 text-sm text-gray-500">{msg.intencion || '-'}</td>
                                    <td className="px-6 py-4 text-sm">
                                        {msg.sentiment && (
                                            <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                                                msg.sentiment.toLowerCase().includes('neg') ? 'bg-red-100 text-red-800' :
                                                msg.sentiment.toLowerCase().includes('pos') ? 'bg-green-100 text-green-800' :
                                                'bg-gray-100 text-gray-800'
                                            }`}>
                                                {msg.sentiment}
                                            </span>
                                        )}
                                    </td>
                                     <td className="px-6 py-4 text-sm text-center">
                                        {msg.is_servilinea ? (
                                            <span title="Conversación redirigida a Servilínea">
                                                <PhoneCall size={16} className="text-blue-500 inline" />
                                            </span>
                                        ) : (
                                            <span className="text-gray-300">-</span>
                                        )}
                                    </td>
                                    <td className="px-6 py-4 text-sm text-right">
                                        {!threadId && (
                                            <button 
                                                onClick={() => { setThreadId(msg.thread_id); setPage(1); }}
                                                className="text-blue-600 hover:text-blue-900 text-xs font-medium"
                                                title="Ver conversación completa"
                                            >
                                                Ver hilo
                                            </button>
                                        )}
                                    </td>
                                </tr>
                            ))
                        )}

                    </tbody>
                </table>
            </div>

            {/* Pagination */}
            <div className="p-4 border-t border-gray-100 flex justify-between items-center bg-gray-50">
                <span className="text-sm text-gray-500">
                    Mostrando {(page-1)*20 + 1} - {Math.min(page*20, total)} de {total}
                </span>
                <div className="flex space-x-2">
                    <button 
                        onClick={() => setPage(p => Math.max(1, p-1))}
                        disabled={page === 1}
                        className="p-2 border border-gray-300 rounded-md bg-white disabled:opacity-50 hover:bg-gray-50"
                    >
                        <ChevronLeft size={16} />
                    </button>
                    <button 
                        onClick={() => setPage(p => Math.min(totalPages, p+1))}
                        disabled={page === totalPages}
                        className="p-2 border border-gray-300 rounded-md bg-white disabled:opacity-50 hover:bg-gray-50"
                    >
                        <ChevronRight size={16} />
                    </button>
                </div>
            </div>
        </div>
    );
};
