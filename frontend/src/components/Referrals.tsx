import { useEffect, useState } from 'react';
import { api } from '../services/api';
import { PhoneCall, ChevronLeft, ChevronRight, ArrowUpDown } from 'lucide-react';

interface ReferralsProps {
    onNavigateToThread?: (threadId: string) => void;
    startDate?: string;
    endDate?: string;
}

export const Referrals = ({ onNavigateToThread, startDate, endDate }: ReferralsProps) => {
    const [referrals, setReferrals] = useState<any[]>([]);
    const [loading, setLoading] = useState(true);
    const [page, setPage] = useState(1);
    const [total, setTotal] = useState(0);
    const limit = 10;
    
    const [sortConfig, setSortConfig] = useState<{ key: string; direction: 'asc' | 'desc' } | null>(null);

    useEffect(() => {
        setLoading(true);
        api.getReferrals({ page, limit, start_date: startDate, end_date: endDate }).then(res => {
            setReferrals(res.data);
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

    const sortedReferrals = [...referrals].sort((a, b) => {
        if (!sortConfig) return 0;
        const aVal = a[sortConfig.key] || '';
        const bVal = b[sortConfig.key] || '';
        if (aVal < bVal) return sortConfig.direction === 'asc' ? -1 : 1;
        if (aVal > bVal) return sortConfig.direction === 'asc' ? 1 : -1;
        return 0;
    });

    const totalPages = Math.ceil(total / limit);

    if (loading && page === 1) return <div className="p-8 text-center text-gray-500">Cargando análisis de Servilínea...</div>;

    if (!loading && referrals.length === 0) return (
        <div className="flex flex-col items-center justify-center h-96 text-gray-400">
            <PhoneCall size={48} className="mb-4 opacity-50" />
            <p>No se han detectado desvíos a Servilínea.</p>
        </div>
    );

    return (
        <div className="bg-white rounded-lg shadow-sm border border-gray-100 overflow-hidden flex flex-col h-full">
            <div className="p-4 border-b border-gray-100 bg-blue-50 flex justify-between items-center">
                <h3 className="text-lg font-medium text-blue-800 flex items-center gap-2">
                    <PhoneCall size={20} />
                    Desvíos a Servilínea ({total})
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
                            <th className="px-6 py-3 text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100" onClick={() => handleSort('customer_request')}>
                                <div className="flex items-center gap-1">Solicitud Cliente <ArrowUpDown size={12} /></div>
                            </th>
                            <th className="px-6 py-3 text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100" onClick={() => handleSort('referral_response')}>
                                <div className="flex items-center gap-1">Respuesta IA <ArrowUpDown size={12} /></div>
                            </th>
                            <th className="px-6 py-3 text-xs font-medium text-gray-500 uppercase tracking-wider">Int./Prod.</th>
                            <th className="px-6 py-3 text-xs font-medium text-gray-500 uppercase tracking-wider">Acciones</th>
                        </tr>
                    </thead>
                    <tbody className="divide-y divide-gray-100">
                        {loading ? (
                             Array.from({ length: 5 }).map((_, i) => (
                                <tr key={i} className="animate-pulse">
                                    <td colSpan={6} className="px-6 py-4"><div className="h-4 bg-gray-200 rounded w-full"></div></td>
                                </tr>
                            ))
                        ) : (
                            sortedReferrals.map((ref) => (
                                <tr key={ref.thread_id} className="hover:bg-gray-50">
                                    <td className="px-6 py-4 text-sm font-mono text-gray-600 whitespace-nowrap">
                                        <span className="cursor-pointer border-b border-dotted border-gray-400 hover:text-blue-600" onClick={() => navigator.clipboard.writeText(ref.thread_id)} title="Copiar ID">
                                            {ref.thread_id}
                                        </span>
                                    </td>
                                    <td className="px-6 py-4 text-sm text-gray-600 whitespace-nowrap">
                                        {ref.fecha ? new Date(ref.fecha).toLocaleDateString() : '-'}
                                    </td>
                                    <td className="px-6 py-4 text-sm text-gray-800 font-medium max-w-xs truncate" title={ref.customer_request}>
                                        {ref.customer_request}
                                    </td>
                                    <td className="px-6 py-4 text-sm text-gray-500 max-w-xs truncate" title={ref.referral_response}>
                                        {ref.referral_response}
                                    </td>
                                    <td className="px-6 py-4 text-sm text-gray-500">
                                        <div className="flex flex-col">
                                            <span className="text-xs">I: {ref.intencion}</span>
                                            <span className="text-xs">P: {ref.product_type}</span>
                                        </div>
                                    </td>
                                    <td className="px-6 py-4 text-sm">
                                        <button 
                                            className="text-blue-600 hover:text-blue-800 text-xs font-medium"
                                            onClick={() => {
                                                if (onNavigateToThread) {
                                                    onNavigateToThread(ref.thread_id);
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
