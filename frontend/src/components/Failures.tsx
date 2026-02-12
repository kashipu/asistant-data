import { useEffect, useState } from 'react';
import { api } from '../services/api';
import { AlertOctagon, ChevronLeft, ChevronRight, ArrowUpDown } from 'lucide-react';

interface FailuresProps {
    onNavigateToThread?: (threadId: string) => void;
    startDate?: string;
    endDate?: string;
}

export const Failures = ({ onNavigateToThread, startDate, endDate }: FailuresProps) => {
    const [failures, setFailures] = useState<any[]>([]);
    const [loading, setLoading] = useState(true);
    const [page, setPage] = useState(1);
    const [total, setTotal] = useState(0);
    const limit = 10;
    
    // Sort state (client-side for now as backend pagination might make server-sort complex without backend changes)
    // Actually backend doesn't support generic sorting yet, so we will sort the CURRENT PAGE or request backend sort if we implemented it.
    // The user wanted simple sort. Since pagination is server side, client sort only sorts the page. 
    // Ideally we should implement server sort. The endpoint in main.py for failures didn't have sort params.
    // Let's implement Client Sort for the current page for now, or just Visual columns.
    // User asked for "el sort en las columnas". 
    // Let's add simple client side sort on the displayed data.
    const [sortConfig, setSortConfig] = useState<{ key: string; direction: 'asc' | 'desc' } | null>(null);

    useEffect(() => {
        setLoading(true);
        api.getFailures({ page, limit, start_date: startDate, end_date: endDate }).then(res => {
            setFailures(res.data);
            setTotal(res.total);
            setLoading(false);
        }).catch(err => {
            console.error(err);
            setLoading(false);
        });
    }, [page, startDate, endDate]);

    const handleSort = (key: string) => {
        let direction: 'asc' | 'desc' = 'asc';
        if (sortConfig && sortConfig.key === key && sortConfig.direction === 'asc') {
            direction = 'desc';
        }
        setSortConfig({ key, direction });
    };

    const sortedFailures = [...failures].sort((a, b) => {
        if (!sortConfig) return 0;
        const aVal = a[sortConfig.key] || '';
        const bVal = b[sortConfig.key] || '';
        if (aVal < bVal) return sortConfig.direction === 'asc' ? -1 : 1;
        if (aVal > bVal) return sortConfig.direction === 'asc' ? 1 : -1;
        return 0;
    });

    const totalPages = Math.ceil(total / limit);

    if (loading && page === 1) return <div className="p-8 text-center text-gray-500">Cargando análisis de fallos...</div>;

    if (!loading && failures.length === 0) return (
        <div className="flex flex-col items-center justify-center h-96 text-gray-400">
            <AlertOctagon size={48} className="mb-4 opacity-50" />
            <p>No se han detectado fallos críticos.</p>
        </div>
    );

    return (
        <div className="bg-white rounded-lg shadow-sm border border-gray-100 overflow-hidden flex flex-col h-full">
            <div className="p-4 border-b border-gray-100 bg-red-50 flex justify-between items-center">
                <h3 className="text-lg font-medium text-red-800 flex items-center gap-2">
                    <AlertOctagon size={20} />
                    Fallos Detectados ({total})
                </h3>
            </div>
            <div className="flex-1 overflow-auto">
                <table className="w-full text-left border-collapse">
                    <thead className="bg-gray-50 sticky top-0 z-10">
                        <tr>
                            <th className="px-6 py-3 text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100" onClick={() => handleSort('thread_id')}>
                                <div className="flex items-center gap-1">Thread ID <ArrowUpDown size={12} /></div>
                            </th>
                            <th className="px-6 py-3 text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100" onClick={() => handleSort('fecha')}>
                                <div className="flex items-center gap-1">Fecha <ArrowUpDown size={12} /></div>
                            </th>
                            <th className="px-6 py-3 text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100" onClick={() => handleSort('criteria')}>
                                <div className="flex items-center gap-1">Criterio(s) <ArrowUpDown size={12} /></div>
                            </th>
                            <th className="px-6 py-3 text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100" onClick={() => handleSort('sentiment')}>
                                <div className="flex items-center gap-1">Sentimiento <ArrowUpDown size={12} /></div>
                            </th>
                            <th className="px-6 py-3 text-xs font-medium text-gray-500 uppercase tracking-wider">Último Mensaje Usuario</th>
                            <th className="px-6 py-3 text-xs font-medium text-gray-500 uppercase tracking-wider">Int./Prod.</th>
                            <th className="px-6 py-3 text-xs font-medium text-gray-500 uppercase tracking-wider">Acciones</th>
                        </tr>
                    </thead>
                    <tbody className="divide-y divide-gray-100">
                        {loading ? (
                             Array.from({ length: 5 }).map((_, i) => (
                                <tr key={i} className="animate-pulse">
                                    <td colSpan={7} className="px-6 py-4"><div className="h-4 bg-gray-200 rounded w-full"></div></td>
                                </tr>
                            ))
                        ) : (
                            sortedFailures.map((fail) => (
                                <tr key={fail.thread_id} className="hover:bg-gray-50">
                                    <td className="px-6 py-4 text-sm font-mono text-gray-600 whitespace-nowrap">
                                        <span className="cursor-pointer border-b border-dotted border-gray-400 hover:text-blue-600" onClick={() => navigator.clipboard.writeText(fail.thread_id)} title="Copiar ID">
                                            {fail.thread_id}
                                        </span>
                                    </td>
                                    <td className="px-6 py-4 text-sm text-gray-600 whitespace-nowrap">
                                        {fail.fecha ? new Date(fail.fecha).toLocaleDateString() : '-'}
                                    </td>
                                    <td className="px-6 py-4 text-sm text-red-600 font-medium">
                                        {fail.criteria}
                                    </td>
                                    <td className="px-6 py-4 text-sm">
                                         <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                                            fail.sentiment === 'negativo' ? 'bg-red-100 text-red-800' :
                                            fail.sentiment === 'positivo' ? 'bg-green-100 text-green-800' :
                                            'bg-yellow-100 text-yellow-800'
                                        }`}>
                                            {fail.sentiment || 'N/A'}
                                        </span>
                                    </td>
                                    <td className="px-6 py-4 text-sm text-gray-600 max-w-xs truncate" title={fail.last_user_message}>
                                        {fail.last_user_message || '-'}
                                    </td>
                                    <td className="px-6 py-4 text-sm text-gray-500">
                                        <div className="flex flex-col">
                                            <span className="text-xs">I: {fail.intencion}</span>
                                            <span className="text-xs">P: {fail.product_type}</span>
                                        </div>
                                    </td>
                                    <td className="px-6 py-4 text-sm">
                                        <button 
                                            className="text-blue-600 hover:text-blue-800 text-xs font-medium"
                                            onClick={() => {
                                                if (onNavigateToThread) {
                                                    onNavigateToThread(fail.thread_id);
                                                }
                                            }}
                                        >
                                            Ver conversación
                                        </button>
                                    </td>
                                </tr>
                            ))
                        )}
                    </tbody>
                </table>
            </div>
            
            {/* Pagination Controls */}
            {totalPages > 1 && (
                <div className="p-4 border-t border-gray-100 flex justify-between items-center bg-gray-50">
                    <span className="text-sm text-gray-500">
                        Página {page} de {totalPages}
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
            )}
        </div>
    );
};
