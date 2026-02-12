
import { useEffect, useState } from 'react';
import { api } from '../services/api';
import { Loader2, ThumbsUp, ThumbsDown, MessageSquare } from "lucide-react";

interface SurveyData {
    stats: {
        total: number;
        useful: number;
        not_useful: number;
    };
    conversations: Array<{
        thread_id: string;
        date: string;
        feedback: string;
        status: string;
    }>;
}

interface SurveyPanelProps {
    onNavigateToThread?: (threadId: string) => void;
    startDate?: string;
    endDate?: string;
}

export function SurveyPanel({ onNavigateToThread, startDate, endDate }: SurveyPanelProps) {
  const [data, setData] = useState<SurveyData | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const loadData = async () => {
      setLoading(true);
      try {
        const result = await api.getSurveys(startDate, endDate);
        setData(result);
      } catch (error) {
        console.error("Failed to load survey data:", error);
      } finally {
        setLoading(false);
      }
    };
    loadData();
  }, [startDate, endDate]);

  if (loading || !data) {
    return (
      <div className="flex justify-center p-8">
        <Loader2 className="h-8 w-8 animate-spin text-blue-500" />
      </div>
    );
  }

  const { stats, conversations } = data;
  const usefulPct = stats.total > 0 ? Math.round((stats.useful / stats.total) * 100) : 0;
  const notUsefulPct = stats.total > 0 ? Math.round((stats.not_useful / stats.total) * 100) : 0;

  return (
    <div className="space-y-6 mt-6">
        
      {/* KPI Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="bg-white p-4 rounded-lg shadow-sm border border-gray-100 flex items-center gap-4">
            <div className="p-3 bg-blue-100 text-blue-600 rounded-full">
                <MessageSquare size={24} />
            </div>
            <div>
                <p className="text-sm text-gray-500 font-medium">Total Encuestas</p>
                <p className="text-2xl font-bold text-gray-900">{stats.total}</p>
            </div>
        </div>
        
        <div className="bg-white p-4 rounded-lg shadow-sm border border-gray-100 flex items-center gap-4">
            <div className="p-3 bg-green-100 text-green-600 rounded-full">
                <ThumbsUp size={24} />
            </div>
            <div>
                <p className="text-sm text-gray-500 font-medium">Útil</p>
                <div className="flex items-baseline gap-2">
                    <p className="text-2xl font-bold text-gray-900">{stats.useful}</p>
                    <span className="text-sm text-green-600 font-medium">({usefulPct}%)</span>
                </div>
            </div>
        </div>

        <div className="bg-white p-4 rounded-lg shadow-sm border border-gray-100 flex items-center gap-4">
            <div className="p-3 bg-red-100 text-red-600 rounded-full">
                <ThumbsDown size={24} />
            </div>
            <div>
                <p className="text-sm text-gray-500 font-medium">No Útil</p>
                <div className="flex items-baseline gap-2">
                    <p className="text-2xl font-bold text-gray-900">{stats.not_useful}</p>
                    <span className="text-sm text-red-600 font-medium">({notUsefulPct}%)</span>
                </div>
            </div>
        </div>
      </div>

      {/* Feedback Table */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-100 overflow-hidden">
        <div className="p-4 border-b border-gray-100 bg-gray-50">
            <h3 className="text-lg font-semibold text-gray-800">Detalle de Respuestas</h3>
        </div>
        <div className="overflow-x-auto max-h-[500px]">
            <table className="w-full text-left border-collapse">
                <thead className="bg-gray-50 sticky top-0 shadow-sm z-10">
                    <tr>
                        <th className="px-6 py-3 text-xs font-bold text-gray-500 uppercase tracking-wider border-b border-gray-200">Fecha</th>
                        <th className="px-6 py-3 text-xs font-bold text-gray-500 uppercase tracking-wider border-b border-gray-200">Resultado</th>
                        <th className="px-6 py-3 text-xs font-bold text-gray-500 uppercase tracking-wider border-b border-gray-200">ID Conversación</th>
                        <th className="px-6 py-3 text-xs font-bold text-gray-500 uppercase tracking-wider border-b border-gray-200">Mensaje Completo</th>
                    </tr>
                </thead>
                <tbody className="divide-y divide-gray-100">
                    {conversations.map((row, idx) => (
                        <tr key={idx} className="hover:bg-gray-50">
                            <td className="px-6 py-4 text-sm text-gray-500 whitespace-nowrap">{row.date}</td>
                            <td className="px-6 py-4 text-sm">
                                {row.status === 'useful' ? (
                                    <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800 gap-1">
                                        <ThumbsUp size={12} /> Útil
                                    </span>
                                ) : row.status === 'not_useful' ? (
                                    <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-red-100 text-red-800 gap-1">
                                        <ThumbsDown size={12} /> No Útil
                                    </span>
                                ) : (
                                    <span className="text-gray-400">-</span>
                                )}
                            </td>
                            <td className="px-6 py-4 text-sm font-mono text-xs whitespace-nowrap">
                                <button 
                                    onClick={() => onNavigateToThread?.(row.thread_id)}
                                    className="text-blue-600 hover:text-blue-800 hover:underline truncate max-w-[150px] text-left block"
                                    title="Ver conversación completa"
                                >
                                    {row.thread_id.substring(0, 12)}...
                                </button>
                            </td>
                            <td className="px-6 py-4 text-sm text-gray-800 max-w-md truncate" title={row.feedback}>
                                {row.feedback}
                            </td>
                        </tr>
                    ))}
                </tbody>
            </table>
        </div>
      </div>
    </div>
  );
}
