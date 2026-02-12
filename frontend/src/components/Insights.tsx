
import React, { useEffect, useState } from 'react';
import { api } from '../services/api';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell } from 'recharts';
import { MessageSquare, PhoneCall, Zap, TrendingUp, AlertCircle } from 'lucide-react';

interface InsightsData {
  kpis: {
    total_conversations: number;
    avg_messages_per_thread: number;
    total_messages: number;
  };
  empty_threads?: number;
  top_intents: Record<string, number>;
  referrals: {
    total: number;
    top_reasons: Array<{ reason: string; count: number }>;
    recent: Array<{
      thread_id: string;
      customer_request: string;
      referral_response: string;
      intencion: string;
    }>;
  };
}

export const Insights: React.FC = () => {
  const [data, setData] = useState<InsightsData | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const result = await api.getInsights();
        setData(result);
      } catch (error) {
        console.error("Error fetching insights:", error);
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, []);

  if (loading || !data) {
    return (
      <div className="p-8 flex justify-center items-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  // Transform top intents for chart
  const intentData = Object.entries(data.top_intents)
    .slice(0, 10)
    .map(([name, value]) => ({ 
      name: name ? name : 'Sin Clasificar', 
      value 
    }));

  const COLORS = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042', '#8884d8', '#82ca9d', '#ffc658', '#8dd1e1', '#a4de6c', '#d0ed57'];

  return (
    <div className="space-y-8">
      {/* Header Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-100 flex items-center space-x-4">
          <div className="p-3 rounded-full bg-blue-100 text-blue-600">
            <MessageSquare className="w-6 h-6" />
          </div>
          <div>
            <p className="text-sm text-gray-500 font-medium">Conversaciones</p>
            <h3 className="text-2xl font-bold text-gray-900">{data.kpis.total_conversations.toLocaleString()}</h3>
          </div>
        </div>

        <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-100 flex items-center space-x-4">
           <div className="p-3 rounded-full bg-purple-100 text-purple-600">
            <TrendingUp className="w-6 h-6" />
          </div>
          <div>
            <p className="text-sm text-gray-500 font-medium">Promedio Mensajes</p>
            <h3 className="text-2xl font-bold text-gray-900">{data.kpis.avg_messages_per_thread}</h3>
          </div>
        </div>

        <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-100 flex items-center space-x-4">
           <div className="p-3 rounded-full bg-orange-100 text-orange-600">
            <PhoneCall className="w-6 h-6" />
          </div>
          <div>
            <h3 className="text-2xl font-bold text-gray-900">{data.referrals.total.toLocaleString()}</h3>
          </div>
        </div>

        <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-100 flex items-center space-x-4">
           <div className="p-3 rounded-full bg-gray-100 text-gray-600">
            <AlertCircle className="w-6 h-6" />
          </div>
          <div>
            <p className="text-sm text-gray-500 font-medium">Conversaciones con Msjs Vacíos</p>
            <h3 className="text-2xl font-bold text-gray-900">{(data.empty_threads || 0).toLocaleString()}</h3>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* Top Intents Chart */}
        <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-100">
          <h3 className="text-lg font-bold text-gray-800 mb-6 flex items-center gap-2">
            <Zap className="w-5 h-5 text-yellow-500" />
            Top Categorias
          </h3>
          <div className="h-80">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={intentData} layout="vertical" margin={{ top: 5, right: 30, left: 40, bottom: 5 }}>
                <CartesianGrid strokeDasharray="3 3" horizontal={true} vertical={false} />
                <XAxis type="number" />
                <YAxis dataKey="name" type="category" width={150} tick={{fontSize: 12}} />
                <Tooltip />
                <Bar dataKey="value" radius={[0, 4, 4, 0]}>
                  {intentData.map((_, index) => (
                    <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Top Referral Reasons */}
        <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-100 flex flex-col">
            <h3 className="text-lg font-bold text-gray-800 mb-6 flex items-center gap-2">
                <AlertCircle className="w-5 h-5 text-red-500" />
                Razones de Redirección (Top 10)
            </h3>
            <div className="overflow-auto flex-1">
                <table className="w-full text-sm text-left text-gray-500">
                    <thead className="text-xs text-gray-700 uppercase bg-gray-50">
                        <tr>
                            <th className="px-4 py-3">Razón Probable (Último Msj Usuario)</th>
                            <th className="px-4 py-3 text-right">Cantidad</th>
                        </tr>
                    </thead>
                    <tbody>
                        {data.referrals.top_reasons.map((item, idx) => (
                            <tr key={idx} className="bg-white border-b hover:bg-gray-50">
                                <td className="px-4 py-3 font-medium text-gray-900 truncate max-w-xs" title={item.reason}>
                                    {item.reason}
                                </td>
                                <td className="px-4 py-3 text-right">
                                    {item.count}
                                </td>
                            </tr>
                        ))}
                    </tbody>
                </table>
            </div>
        </div>
      </div>

       {/* Recent Redirections */}
       <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-100">
          <h3 className="text-lg font-bold text-gray-800 mb-6">Redirecciones Recientes</h3>
          <div className="overflow-x-auto">
            <table className="w-full text-sm text-left text-gray-500">
                <thead className="text-xs text-gray-700 uppercase bg-gray-50">
                    <tr>
                        <th className="px-6 py-3">ID Conversación</th>
                        <th className="px-6 py-3">Intención</th>
                        <th className="px-6 py-3">Mensaje Cliente</th>
                        <th className="px-6 py-3">Respuesta Bot</th>
                    </tr>
                </thead>
                <tbody>
                    {data.referrals.recent.map((item) => (
                        <tr key={item.thread_id} className="bg-white border-b hover:bg-gray-50">
                            <td className="px-6 py-4 font-medium text-gray-900 whitespace-nowrap">
                                {item.thread_id}
                            </td>
                            <td className="px-6 py-4">
                                <span className="bg-gray-100 text-gray-800 text-xs font-medium px-2.5 py-0.5 rounded border border-gray-500">
                                    {item.intencion || 'N/A'}
                                </span>
                            </td>
                            <td className="px-6 py-4 max-w-md truncate" title={item.customer_request}>
                                {item.customer_request}
                            </td>
                             <td className="px-6 py-4 max-w-md truncate" title={item.referral_response}>
                                {item.referral_response}
                            </td>
                        </tr>
                    ))}
                </tbody>
            </table>
          </div>
       </div>
    </div>
  );
};
