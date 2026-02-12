
import { useEffect, useState } from 'react';
import { api } from '../services/api';
import { Loader2, Table, ArrowUpDown, ArrowUp, ArrowDown } from "lucide-react";

interface SummaryData {
  category: string;
  intention: string;
  total_interactions: number;
  unique_conversations: number;
  human_msgs: number;
  ai_msgs: number;
  tool_msgs: number;
  positive: number;
  neutral: number;
  negative: number;
  servilinea_referrals: number;
}

type SortKey = keyof SummaryData;
type SortDirection = 'asc' | 'desc';

interface SummaryTableProps {
  startDate?: string;
  endDate?: string;
}

export function SummaryTable({ startDate, endDate }: SummaryTableProps) {
  const [data, setData] = useState<SummaryData[]>([]);
  const [loading, setLoading] = useState(true);
  const [sortConfig, setSortConfig] = useState<{ key: SortKey; direction: SortDirection }>({
    key: 'unique_conversations',
    direction: 'desc'
  });

  useEffect(() => {
    const loadData = async () => {
      setLoading(true);
      try {
        const result = await api.getSummary(startDate, endDate);
        setData(result);
      } catch (error) {
        console.error("Failed to load summary data:", error);
      } finally {
        setLoading(false);
      }
    };
    loadData();
  }, [startDate, endDate]);

  const handleSort = (key: SortKey) => {
    let direction: SortDirection = 'desc';
    if (sortConfig.key === key && sortConfig.direction === 'desc') {
      direction = 'asc';
    }
    setSortConfig({ key, direction });
  };

  const sortedData = [...data].sort((a, b) => {
    const aValue = a[sortConfig.key];
    const bValue = b[sortConfig.key];
    
    // Check if values are strings
    if (typeof aValue === 'string' && typeof bValue === 'string') {
        const comparison = aValue.localeCompare(bValue);
        return sortConfig.direction === 'asc' ? comparison : -comparison;
    }
    
    // Numeric sort
    if (aValue < bValue) return sortConfig.direction === 'asc' ? -1 : 1;
    if (aValue > bValue) return sortConfig.direction === 'asc' ? 1 : -1;
    return 0;
  });

  const getSortIcon = (columnKey: SortKey) => {
    if (sortConfig.key !== columnKey) return <ArrowUpDown size={14} className="text-gray-300" />;
    return sortConfig.direction === 'asc' 
      ? <ArrowUp size={14} className="text-blue-500" /> 
      : <ArrowDown size={14} className="text-blue-500" />;
  };

  if (loading) {
    return (
      <div className="mt-6 bg-white p-6 rounded-lg shadow-sm border border-gray-100 flex justify-center">
        <Loader2 className="h-8 w-8 animate-spin text-blue-500" />
      </div>
    );
  }

  // Calculate totals
  const totals = data.reduce((acc, curr) => ({
    total_interactions: acc.total_interactions + curr.total_interactions,
    unique_conversations: acc.unique_conversations + curr.unique_conversations,
    human_msgs: acc.human_msgs + curr.human_msgs,
    ai_msgs: acc.ai_msgs + curr.ai_msgs,
    tool_msgs: acc.tool_msgs + curr.tool_msgs,
    positive: acc.positive + curr.positive,
    neutral: acc.neutral + curr.neutral,
    negative: acc.negative + curr.negative,
    servilinea_referrals: acc.servilinea_referrals + curr.servilinea_referrals,
    category: 'TOTAL',
    intention: ''
  }), {
    total_interactions: 0,
    unique_conversations: 0,
    human_msgs: 0,
    ai_msgs: 0,
    tool_msgs: 0,
    positive: 0,
    neutral: 0,
    negative: 0,
    servilinea_referrals: 0,
    category: 'TOTAL',
    intention: ''
  });

  return (
    <div className="mt-6 bg-white rounded-lg shadow-sm border border-gray-100 overflow-hidden">
      <div className="p-4 border-b border-gray-100 flex justify-between items-center bg-gray-50">
         <h3 className="text-lg font-semibold text-gray-800 flex items-center gap-2">
            <Table size={20} className="text-gray-500" />
            Resumen por Categoría e Intención
         </h3>
         <div className="text-xs text-gray-400">
             Clic en encabezados para ordenar
         </div>
      </div>
      <div className="overflow-x-auto max-h-[600px]">
        <table className="w-full text-left border-collapse relative">
            <thead className="bg-gray-50 sticky top-0 z-10 shadow-sm">
              <tr>
                <th rowSpan={2} 
                    className="px-6 py-3 text-xs font-bold text-gray-500 uppercase tracking-wider border-b border-gray-200 bg-gray-50 cursor-pointer hover:bg-gray-100"
                    onClick={() => handleSort('category')}>
                    <div className="flex items-center gap-1">Categoría {getSortIcon('category')}</div>
                </th>
                <th rowSpan={2} 
                    className="px-6 py-3 text-xs font-bold text-gray-500 uppercase tracking-wider border-b border-gray-200 bg-gray-50 cursor-pointer hover:bg-gray-100"
                    onClick={() => handleSort('intention')}>
                    <div className="flex items-center gap-1">Intención {getSortIcon('intention')}</div>
                </th>
                <th rowSpan={2} 
                    className="px-6 py-3 text-xs font-bold text-gray-900 uppercase tracking-wider text-right border-b border-gray-200 bg-gray-50 cursor-pointer hover:bg-gray-100"
                    onClick={() => handleSort('unique_conversations')}>
                    <div className="flex items-center justify-end gap-1">Conversaciones {getSortIcon('unique_conversations')}</div>
                </th>
                <th colSpan={3} className="px-6 py-2 text-xs font-bold text-gray-500 uppercase tracking-wider text-center border-b border-gray-200 bg-gray-50">Mensajes por Tipo</th>
                <th colSpan={3} className="px-6 py-2 text-xs font-bold text-gray-500 uppercase tracking-wider text-center border-b border-gray-200 bg-gray-50">Sentimiento (Humano)</th>
                <th rowSpan={2} 
                    className="px-6 py-3 text-xs font-bold text-blue-600 uppercase tracking-wider text-right border-b border-gray-200 bg-gray-50 cursor-pointer hover:bg-gray-100"
                    onClick={() => handleSort('servilinea_referrals')}>
                    <div className="flex items-center justify-end gap-1">Ref. Servilínea {getSortIcon('servilinea_referrals')}</div>
                </th>
              </tr>
              <tr>
                <th className="px-4 py-2 text-xs font-medium text-gray-500 uppercase text-right bg-gray-50 border-b border-gray-200 cursor-pointer" onClick={() => handleSort('human_msgs')}>Humano</th>
                <th className="px-4 py-2 text-xs font-medium text-gray-500 uppercase text-right bg-gray-50 border-b border-gray-200 cursor-pointer" onClick={() => handleSort('ai_msgs')}>IA</th>
                <th className="px-4 py-2 text-xs font-medium text-gray-500 uppercase text-right bg-gray-50 border-b border-gray-200 cursor-pointer" onClick={() => handleSort('tool_msgs')}>Tool</th>
                <th className="px-4 py-2 text-xs font-medium text-green-600 uppercase text-right bg-gray-50 border-b border-gray-200 cursor-pointer" onClick={() => handleSort('positive')}>Pos</th>
                <th className="px-4 py-2 text-xs font-medium text-gray-500 uppercase text-right bg-gray-50 border-b border-gray-200 cursor-pointer" onClick={() => handleSort('neutral')}>Neu</th>
                <th className="px-4 py-2 text-xs font-medium text-red-600 uppercase text-right bg-gray-50 border-b border-gray-200 cursor-pointer" onClick={() => handleSort('negative')}>Neg</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {sortedData.map((row, idx) => (
                <tr key={`${row.category}-${row.intention}-${idx}`} className="hover:bg-gray-50 transition-colors">
                  <td className="px-6 py-4 text-sm font-medium text-gray-900 capitalize border-r border-gray-100">
                      {row.category === 'uncategorized' ? 'Sin Categoría' : row.category}
                  </td>
                  <td className="px-6 py-4 text-sm text-gray-600 capitalize border-r border-gray-100">
                      {row.intention}
                  </td>
                  <td className="px-6 py-4 text-sm font-bold text-gray-900 text-right border-r border-gray-100">{row.unique_conversations}</td>
                  
                  <td className="px-4 py-4 text-sm text-gray-600 text-right">{row.human_msgs}</td>
                  <td className="px-4 py-4 text-sm text-gray-600 text-right">{row.ai_msgs}</td>
                  <td className="px-4 py-4 text-sm text-gray-600 text-right border-r border-gray-100">{row.tool_msgs}</td>
                  
                  <td className="px-4 py-4 text-sm text-green-700 text-right bg-green-50/30">{row.positive}</td>
                  <td className="px-4 py-4 text-sm text-gray-600 text-right">{row.neutral}</td>
                  <td className="px-4 py-4 text-sm text-red-700 text-right bg-red-50/30 border-r border-gray-100">{row.negative}</td>
                  
                  <td className="px-6 py-4 text-sm font-bold text-blue-600 text-right bg-blue-50/50">{row.servilinea_referrals}</td>
                </tr>
              ))}
              <tr className="bg-gray-100 font-bold border-t-2 border-gray-200 sticky bottom-0 z-10 shadow-inner">
                <td className="px-6 py-4 text-sm text-gray-900" colSpan={2}>TOTAL ({sortedData.length} grupos)</td>
                <td className="px-6 py-4 text-sm text-gray-900 text-right border-r border-gray-200">{totals.unique_conversations}</td>
                
                <td className="px-4 py-4 text-sm text-gray-900 text-right">{totals.human_msgs}</td>
                <td className="px-4 py-4 text-sm text-gray-900 text-right">{totals.ai_msgs}</td>
                <td className="px-4 py-4 text-sm text-gray-900 text-right border-r border-gray-200">{totals.tool_msgs}</td>
                
                <td className="px-4 py-4 text-sm text-gray-900 text-right">{totals.positive}</td>
                <td className="px-4 py-4 text-sm text-gray-900 text-right">{totals.neutral}</td>
                <td className="px-4 py-4 text-sm text-gray-900 text-right border-r border-gray-200">{totals.negative}</td>
                
                <td className="px-6 py-4 text-sm text-blue-700 text-right">{totals.servilinea_referrals}</td>
              </tr>
            </tbody>
        </table>
      </div>
    </div>
  );
}
