import { useEffect, useState } from 'react';
import { api } from '../services/api';
import { Loader2, AlertCircle, PhoneCall, MessageCircleWarning, Database, ArrowLeft, ArrowRight, ArrowUpDown } from "lucide-react";

interface UncategorizedThread {
  thread_id: string;
  sample_text: string;
  msg_count: number;
  date: string;
  is_servilinea: boolean;
  has_empty_msg: boolean;
}

interface Stats {
  servilinea: number;
  empty_msgs: number;
}

interface UncategorizedPanelProps {
  onNavigateToThread?: (threadId: string) => void;
  startDate?: string;
  endDate?: string;
}

export function UncategorizedPanel({ onNavigateToThread, startDate, endDate }: UncategorizedPanelProps) {
  const [data, setData] = useState<UncategorizedThread[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [page, setPage] = useState(1);
  const [limit] = useState(20);
  const [total, setTotal] = useState(0);
  const [stats, setStats] = useState<Stats>({ servilinea: 0, empty_msgs: 0 });
  
  const [sortConfig, setSortConfig] = useState<{ key: string; direction: 'asc' | 'desc' } | null>(null);

  useEffect(() => {
    const loadData = async () => {
      setLoading(true);
      try {
        const result = await api.getUncategorized(page, limit, startDate, endDate);
        // Handle both old list format and new dict format for backward compat during dev
        if (Array.isArray(result)) {
             setData(result);
             setTotal(result.length);
        } else {
             setData(result.data);
             setTotal(result.total);
             setStats(result.stats);
        }
      } catch (error) {
        console.error("Failed to load uncategorized data:", error);
        setError("Error cargando datos. Verifique la consola.");
      } finally {
        setLoading(false);
      }
    };
    loadData();
  }, [page, limit, startDate, endDate]);

  const handleSort = (key: string) => {
      let direction: 'asc' | 'desc' = 'asc';
      if (sortConfig && sortConfig.key === key && sortConfig.direction === 'asc') {
          direction = 'desc';
      }
      setSortConfig({ key, direction });
  };

  const sortedData = [...data].sort((a, b) => {
      if (!sortConfig) return 0;
      const aVal = (a as any)[sortConfig.key] || '';
      const bVal = (b as any)[sortConfig.key] || '';
      if (aVal < bVal) return sortConfig.direction === 'asc' ? -1 : 1;
      if (aVal > bVal) return sortConfig.direction === 'asc' ? 1 : -1;
      return 0;
  });

  const totalPages = Math.ceil(total / limit);

  if (error) {
    return (
      <div className="p-8 text-center text-red-500">
        <AlertCircle size={32} className="mx-auto mb-2" />
        <p>{error}</p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-100 flex items-center space-x-4">
            <div className="p-3 rounded-full bg-orange-100 text-orange-600">
              <Database className="w-6 h-6" />
            </div>
            <div>
              <p className="text-sm text-gray-500 font-medium">Total Sin Clasificar</p>
              <h3 className="text-2xl font-bold text-gray-900">{total.toLocaleString()}</h3>
            </div>
          </div>

          <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-100 flex items-center space-x-4">
             <div className="p-3 rounded-full bg-blue-100 text-blue-600">
              <PhoneCall className="w-6 h-6" />
            </div>
            <div>
              <p className="text-sm text-gray-500 font-medium">A Servilínea</p>
              <h3 className="text-2xl font-bold text-gray-900">{stats.servilinea.toLocaleString()}</h3>
            </div>
          </div>

          <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-100 flex items-center space-x-4">
             <div className="p-3 rounded-full bg-gray-100 text-gray-600">
              <MessageCircleWarning className="w-6 h-6" />
            </div>
            <div>
              <p className="text-sm text-gray-500 font-medium">Con Mensajes Vacíos</p>
              <h3 className="text-2xl font-bold text-gray-900">{stats.empty_msgs.toLocaleString()}</h3>
            </div>
          </div>
      </div>

      {/* Table */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-100 overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse">
            <thead className="bg-gray-50 border-b border-gray-200">
              <tr>
                <th className="px-6 py-3 text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100" onClick={() => handleSort('thread_id')}>
                    <div className="flex items-center gap-1">Conversación ID <ArrowUpDown size={12} /></div>
                </th>
                <th className="px-6 py-3 text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100" onClick={() => handleSort('date')}>
                    <div className="flex items-center gap-1">Fecha <ArrowUpDown size={12} /></div>
                </th>
                <th className="px-6 py-3 text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100" onClick={() => handleSort('sample_text')}>
                    <div className="flex items-center gap-1">Muestra de Texto <ArrowUpDown size={12} /></div>
                </th>
                <th className="px-6 py-3 text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100" onClick={() => handleSort('msg_count')}>
                    <div className="flex items-center gap-1">Mensajes <ArrowUpDown size={12} /></div>
                </th>
                <th className="px-6 py-3 text-xs font-medium text-gray-500 uppercase tracking-wider">Etiquetas</th>
                <th className="px-6 py-3 text-xs font-medium text-gray-500 uppercase tracking-wider">Acción</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {loading ? (
                <tr>
                  <td colSpan={6} className="px-6 py-8 text-center text-gray-500">
                    <Loader2 className="w-6 h-6 animate-spin mx-auto mb-2" />
                    Cargando...
                  </td>
                </tr>
              ) : sortedData.length === 0 ? (
                <tr>
                  <td colSpan={6} className="px-6 py-8 text-center text-gray-500">
                     No se encontraron conversaciones sin clasificar.
                  </td>
                </tr>
              ) : (
                sortedData.map((thread) => (
                  <tr key={thread.thread_id} className="hover:bg-gray-50">
                    <td className="px-6 py-4 text-sm font-mono text-gray-600 whitespace-nowrap">
                        <span className="cursor-pointer border-b border-dotted border-gray-400 hover:text-blue-600" onClick={() => navigator.clipboard.writeText(thread.thread_id)} title="Copiar ID">
                            {thread.thread_id}
                        </span>
                    </td>
                    <td className="px-6 py-4 text-sm text-gray-500 whitespace-nowrap">
                      {thread.date}
                    </td>
                    <td className="px-6 py-4 text-sm text-gray-800 max-w-md truncate" title={thread.sample_text}>
                      {thread.sample_text || <span className="text-gray-400 italic">Sin texto</span>}
                    </td>
                    <td className="px-6 py-4 text-sm text-gray-500">
                      {thread.msg_count}
                    </td>
                    <td className="px-6 py-4 text-sm space-x-1">
                      {thread.is_servilinea && (
                        <span className="px-2 py-0.5 rounded text-xs font-medium bg-blue-100 text-blue-700 border border-blue-200">
                          Servilínea
                        </span>
                      )}
                      {thread.has_empty_msg && (
                        <span className="px-2 py-0.5 rounded text-xs font-medium bg-gray-100 text-gray-600 border border-gray-200">
                          Msg Vacío
                        </span>
                      )}
                    </td>
                    <td className="px-6 py-4 text-sm">
                      <button
                        onClick={() => onNavigateToThread && onNavigateToThread(thread.thread_id)}
                        className="text-blue-600 hover:text-blue-800 font-medium text-xs"
                      >
                        Ver
                      </button>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
        
        {/* Pagination */}
        <div className="p-4 border-t border-gray-100 bg-gray-50 flex items-center justify-between">
           <span className="text-sm text-gray-500">
              Página {page} de {totalPages} ({total} total)
           </span>
           <div className="flex gap-2">
             <button
                onClick={() => setPage(p => Math.max(1, p - 1))}
                disabled={page === 1}
                className="p-2 bg-white border border-gray-300 rounded hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
             >
               <ArrowLeft size={16} />
             </button>
             <button
                onClick={() => setPage(p => Math.min(totalPages, p + 1))}
                disabled={page >= totalPages}
                className="p-2 bg-white border border-gray-300 rounded hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
             >
               <ArrowRight size={16} />
             </button>
           </div>
        </div>
      </div>
    </div>
  );
}
