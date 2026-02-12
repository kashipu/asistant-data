import { useEffect, useState } from 'react';
import { api } from '../services/api';
import { Loader2, AlertCircle, UserCheck, Clock, History, ArrowUpDown, ArrowLeft, ArrowRight } from "lucide-react";

interface AdvisorRequest {
  thread_id: string;
  date: string;
  sample_text: string;
  msg_count: number;
  request_type: string;
}

interface Stats {
  total: number;
  immediate: number;
  after_effort: number;
}

interface AdvisorPanelProps {
  onNavigateToThread?: (threadId: string) => void;
  startDate?: string;
  endDate?: string;
}

export function AdvisorPanel({ onNavigateToThread, startDate, endDate }: AdvisorPanelProps) {
  const [data, setData] = useState<AdvisorRequest[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [stats, setStats] = useState<Stats>({ total: 0, immediate: 0, after_effort: 0 });
  
  // Pagination
  const [page, setPage] = useState(1);
  const [limit] = useState(20);
  
  // Sorting
  const [sortConfig, setSortConfig] = useState<{ key: string; direction: 'asc' | 'desc' } | null>(null);

  useEffect(() => {
    const loadData = async () => {
      setLoading(true);
      try {
        const result = await api.getAdvisors(startDate, endDate);
        setData(result.data);
        setStats(result.stats);
      } catch (error) {
        console.error("Failed to load advisor data:", error);
        setError("Error cargando datos de asesores.");
      } finally {
        setLoading(false);
      }
    };
    loadData();
  }, [startDate, endDate]);

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

  // Client-side pagination since API returns all for now (implied by previous pattern, 
  // though typically we should paginate on backend if large. 
  // Given current backend implementation returns all, we slice here.)
  const totalPages = Math.ceil(sortedData.length / limit);
  const paginatedData = sortedData.slice((page - 1) * limit, page * limit);

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
      {/* KPI Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-100 flex items-center space-x-4">
            <div className="p-3 rounded-full bg-purple-100 text-purple-600">
              <UserCheck className="w-6 h-6" />
            </div>
            <div>
              <p className="text-sm text-gray-500 font-medium">Total Solicitudes</p>
              <h3 className="text-2xl font-bold text-gray-900">{stats.total.toLocaleString()}</h3>
            </div>
          </div>

          <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-100 flex items-center space-x-4">
             <div className="p-3 rounded-full bg-red-100 text-red-600">
              <Clock className="w-6 h-6" />
            </div>
            <div>
              <p className="text-sm text-gray-500 font-medium">De Inmediato</p>
              <h3 className="text-2xl font-bold text-gray-900">{stats.immediate.toLocaleString()}</h3>
              <p className="text-xs text-gray-400">Primeros 2 mensajes</p>
            </div>
          </div>

          <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-100 flex items-center space-x-4">
             <div className="p-3 rounded-full bg-green-100 text-green-600">
              <History className="w-6 h-6" />
            </div>
            <div>
              <p className="text-sm text-gray-500 font-medium">Luego de Intentar</p>
              <h3 className="text-2xl font-bold text-gray-900">{stats.after_effort.toLocaleString()}</h3>
              <p className="text-xs text-gray-400">Despues de interactuar</p>
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
                    <div className="flex items-center gap-1">ID Conversación <ArrowUpDown size={12} /></div>
                </th>
                <th className="px-6 py-3 text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100" onClick={() => handleSort('date')}>
                    <div className="flex items-center gap-1">Fecha <ArrowUpDown size={12} /></div>
                </th>
                 <th className="px-6 py-3 text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100" onClick={() => handleSort('request_type')}>
                    <div className="flex items-center gap-1">Tipo <ArrowUpDown size={12} /></div>
                </th>
                <th className="px-6 py-3 text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100" onClick={() => handleSort('sample_text')}>
                    <div className="flex items-center gap-1">Mensaje <ArrowUpDown size={12} /></div>
                </th>
                <th className="px-6 py-3 text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100" onClick={() => handleSort('msg_count')}>
                    <div className="flex items-center gap-1">Total Msgs <ArrowUpDown size={12} /></div>
                </th>
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
              ) : paginatedData.length === 0 ? (
                <tr>
                  <td colSpan={6} className="px-6 py-8 text-center text-gray-500">
                     No se encontraron solicitudes de asesor.
                  </td>
                </tr>
              ) : (
                paginatedData.map((row) => (
                  <tr key={row.thread_id} className="hover:bg-gray-50">
                    <td className="px-6 py-4 text-sm font-mono text-gray-600 whitespace-nowrap">
                        <span className="cursor-pointer border-b border-dotted border-gray-400 hover:text-blue-600" onClick={() => navigator.clipboard.writeText(row.thread_id)} title="Copiar ID">
                            {row.thread_id}
                        </span>
                    </td>
                    <td className="px-6 py-4 text-sm text-gray-500 whitespace-nowrap">
                      {row.date}
                    </td>
                    <td className="px-6 py-4 text-sm whitespace-nowrap">
                      <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                          row.request_type === 'Inmediato' 
                          ? 'bg-red-100 text-red-700' 
                          : 'bg-green-100 text-green-700'
                      }`}>
                          {row.request_type}
                      </span>
                    </td>
                    <td className="px-6 py-4 text-sm text-gray-800 max-w-md truncate" title={row.sample_text}>
                      {row.sample_text}
                    </td>
                    <td className="px-6 py-4 text-sm text-gray-500 text-center">
                      {row.msg_count}
                    </td>
                    <td className="px-6 py-4 text-sm">
                      <button
                        onClick={() => onNavigateToThread && onNavigateToThread(row.thread_id)}
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
              Página {page} de {totalPages} ({sortedData.length} total)
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
