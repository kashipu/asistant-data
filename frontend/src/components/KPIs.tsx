
import React from 'react';
import { MessageSquare, Users, Activity, Database } from 'lucide-react';

interface KPIData {
  total_conversations: number;
  total_messages: number;
  total_users: number;
  avg_messages_per_thread: number;
  total_input_tokens: number;
  total_output_tokens: number;
}

interface KPIsProps {
  data: KPIData | null;
  loading: boolean;
}

const KpiCard = ({ title, value, icon: Icon, color }: { title: string, value: string | number, icon: any, color: string }) => (
  <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-100 flex items-center space-x-4">
    <div className={`p-3 rounded-full ${color}`}>
      <Icon className="w-6 h-6 text-white" />
    </div>
    <div>
      <p className="text-sm text-gray-500 font-medium uppercase tracking-wider">{title}</p>
      <h3 className="text-2xl font-bold text-gray-900">{value}</h3>
    </div>
  </div>
);

export const KPIs: React.FC<KPIsProps> = ({ data, loading }) => {
  if (loading || !data) {
    return <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 animate-pulse">
        {[1,2,3,4].map(i => <div key={i} className="h-24 bg-gray-200 rounded-lg"></div>)}
    </div>;
  }

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
      <KpiCard 
        title="Conversaciones" 
        value={data.total_conversations.toLocaleString()} 
        icon={MessageSquare} 
        color="bg-blue-500" 
      />
      <KpiCard 
        title="Mensajes Totales" 
        value={data.total_messages.toLocaleString()} 
        icon={Database} 
        color="bg-purple-500" 
      />
      <KpiCard 
        title="Usuarios Únicos" 
        value={data.total_users.toLocaleString()} 
        icon={Users} 
        color="bg-green-500" 
      />
      <KpiCard 
        title="Avg. Msgs/Conv" 
        value={data.avg_messages_per_thread} 
        icon={Activity} 
        color="bg-orange-500" 
      />
    </div>
  );
};
