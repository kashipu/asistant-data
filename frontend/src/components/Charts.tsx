import { useEffect, useState } from 'react';
import { api } from '../services/api';
import {
  XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, AreaChart, Area, BarChart, Bar
} from 'recharts';
import { Loader2, Activity, Clock } from 'lucide-react';

interface ChartsProps {
  startDate?: string;
  endDate?: string;
}

interface BreakdownItem {
  label: string;
  count: number;
}

interface Correlation {
  label: string;
  count: number;
  pct: number;
}

interface Metric {
  id: string;
  label: string;
  count: number;
  pct: number;
  base_label: string;
  explanation: string;
  color: string;
  breakdown?: BreakdownItem[];
  correlation?: Correlation | null;
}

interface DashboardData {
  metrics: Metric[];
  waste_by_category: Array<{
    category: string;
    count: number;
    pct_of_waste: number;
  }>;
}

interface TemporalData {
  daily_volume: Record<string, number>;
  hourly_volume: Record<string, number>;
  heatmap: Array<{ day: string; hour: number; count: number }>;
}

const COLOR_MAP: Record<string, { bg: string; border: string; text: string; pct: string }> = {
  blue:    { bg: 'bg-blue-50',    border: 'border-blue-100',    text: 'text-blue-900',    pct: 'text-blue-600' },
  gray:    { bg: 'bg-gray-50',    border: 'border-gray-100',    text: 'text-gray-700',    pct: 'text-gray-500' },
  indigo:  { bg: 'bg-indigo-50',  border: 'border-indigo-100',  text: 'text-indigo-900',  pct: 'text-indigo-600' },
  emerald: { bg: 'bg-emerald-50', border: 'border-emerald-100', text: 'text-emerald-900', pct: 'text-emerald-600' },
  orange:  { bg: 'bg-orange-50',  border: 'border-orange-100',  text: 'text-orange-900',  pct: 'text-orange-600' },
  purple:  { bg: 'bg-purple-50',  border: 'border-purple-100',  text: 'text-purple-900',  pct: 'text-purple-600' },
  violet:  { bg: 'bg-violet-50',  border: 'border-violet-100',  text: 'text-violet-900',  pct: 'text-violet-600' },
  green:   { bg: 'bg-green-50',   border: 'border-green-100',   text: 'text-green-900',   pct: 'text-green-600' },
  rose:    { bg: 'bg-rose-50',    border: 'border-rose-100',    text: 'text-rose-900',    pct: 'text-rose-600' },
  red:     { bg: 'bg-red-50',     border: 'border-red-100',     text: 'text-red-900',     pct: 'text-red-600' },
};

function N(n: number): string {
  return Math.round(n).toLocaleString('es-CO');
}

export const Charts = ({ startDate, endDate }: ChartsProps) => {
  const [data, setData] = useState<DashboardData | null>(null);
  const [temporalData, setTemporalData] = useState<TemporalData | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchData = async () => {
      setLoading(true);
      try {
        const [dashboard, temp] = await Promise.all([
          api.getFunnel({ start_date: startDate, end_date: endDate }),
          api.getTemporalAnalysis({ start_date: startDate, end_date: endDate }),
        ]);
        setData(dashboard);
        setTemporalData(temp);
      } catch (error) {
        console.error(error);
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, [startDate, endDate]);

  if (loading || !temporalData || !data) return (
    <div className="h-96 flex flex-col items-center justify-center gap-4">
      <Loader2 className="h-10 w-10 animate-spin text-blue-600" />
      <p className="text-gray-500 font-medium animate-pulse">Cargando dashboard...</p>
    </div>
  );

  const dailyData = Object.entries(temporalData.daily_volume)
    .map(([date, count]) => ({ date, count }))
    .sort((a, b) => a.date.localeCompare(b.date));

  const hourlyData = Array.from({ length: 24 }, (_, h) => ({
    hour: `${h.toString().padStart(2, '0')}:00`,
    count: temporalData.hourly_volume[h] || temporalData.hourly_volume[String(h)] || 0,
  }));

  const metrics = data.metrics || [];

  return (
    <div className="space-y-8 animate-in fade-in duration-700 pb-12">

      {/* METRICS GRID */}
      <div className="bg-white rounded-3xl border border-gray-100 shadow-xl overflow-hidden">
        <div className="p-6 border-b border-gray-50 bg-gradient-to-r from-gray-50/50 to-transparent">
          <h3 className="text-lg font-black text-gray-900">Métricas del Chatbot</h3>
          <p className="text-xs text-gray-500 font-medium">Cada métrica muestra su base de cálculo y explicación.</p>
        </div>

        <div className="p-6 grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
          {metrics.map((m) => {
            const c = COLOR_MAP[m.color] || COLOR_MAP.gray;
            const hasExtra = (m.breakdown && m.breakdown.length > 0) || m.correlation;
            return (
              <div
                key={m.id}
                className={`${c.bg} ${c.border} border rounded-2xl p-4 group hover:shadow-md transition-all duration-200 ${hasExtra ? 'row-span-1' : ''}`}
              >
                <div className="text-[10px] font-bold uppercase tracking-widest text-gray-400 mb-1.5">
                  {m.label}
                </div>
                <div className={`text-2xl font-black ${c.text} tabular-nums`}>
                  {N(m.count)}
                </div>
                <div className="flex items-baseline gap-1.5 mt-1">
                  <span className={`text-sm font-black ${c.pct}`}>{m.pct}%</span>
                  <span className="text-[9px] font-semibold text-gray-400">{m.base_label}</span>
                </div>

                {/* Breakdown items */}
                {m.breakdown && m.breakdown.length > 0 && (
                  <div className="mt-2 space-y-1 border-t border-gray-100 pt-2">
                    {m.breakdown.map((b, i) => (
                      <div key={i} className="flex items-center justify-between text-[10px]">
                        <span className="text-gray-600">{b.label}</span>
                        <span className={`font-bold ${c.pct} tabular-nums`}>{N(b.count)}</span>
                      </div>
                    ))}
                  </div>
                )}

                {/* Correlation */}
                {m.correlation && (
                  <div className="mt-2 bg-white/60 rounded-lg px-2 py-1.5 border border-gray-100">
                    <div className="text-[10px] text-gray-500">
                      <span className="font-semibold">{N(m.correlation.count)}</span> ({m.correlation.pct}%) {m.correlation.label.toLowerCase()}
                    </div>
                  </div>
                )}

                <p className="text-[10px] text-gray-400 leading-snug mt-2 border-t border-gray-100 pt-2 group-hover:text-gray-600 transition-colors">
                  {m.explanation}
                </p>
              </div>
            );
          })}
        </div>
      </div>

      {/* TENDENCIA + HORARIO — side by side on large screens */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">

        {/* TENDENCIA CHART */}
        <div className="bg-white p-8 rounded-3xl shadow-sm border border-gray-100">
          <div className="flex items-center justify-between mb-6">
            <div>
              <h3 className="text-lg font-black text-gray-900 leading-tight">Tendencia Diaria</h3>
              <p className="text-xs text-gray-500 font-medium">Volumen de mensajes por día.</p>
            </div>
            <div className="flex items-center gap-2 p-2 bg-blue-50 rounded-xl text-blue-700">
              <Activity size={18} />
            </div>
          </div>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={dailyData}>
                <defs>
                  <linearGradient id="colorCount" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#3B82F6" stopOpacity={0.2}/>
                    <stop offset="95%" stopColor="#3B82F6" stopOpacity={0}/>
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#F3F4F6" />
                <XAxis dataKey="date" axisLine={false} tickLine={false} tick={{fill: '#9CA3AF', fontSize: 10, fontWeight: 'bold'}} />
                <YAxis axisLine={false} tickLine={false} tick={{fill: '#9CA3AF', fontSize: 11, fontWeight: 'bold'}} />
                <Tooltip contentStyle={{borderRadius: '16px', border: 'none', boxShadow: '0 10px 15px -3px rgb(0 0 0 / 0.1)'}} />
                <Area type="monotone" dataKey="count" stroke="#3B82F6" strokeWidth={3} fillOpacity={1} fill="url(#colorCount)" dot={{r: 3, fill: '#3B82F6', strokeWidth: 2, stroke: '#FFF'}} />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* VOLUMEN POR HORA */}
        <div className="bg-white p-8 rounded-3xl shadow-sm border border-gray-100">
          <div className="flex items-center justify-between mb-6">
            <div>
              <h3 className="text-lg font-black text-gray-900 leading-tight">Volumen por Hora</h3>
              <p className="text-xs text-gray-500 font-medium">Distribución horaria de mensajes (hora Colombia).</p>
            </div>
            <div className="flex items-center gap-2 p-2 bg-violet-50 rounded-xl text-violet-700">
              <Clock size={18} />
            </div>
          </div>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={hourlyData}>
                <defs>
                  <linearGradient id="colorHour" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#8B5CF6" stopOpacity={0.8}/>
                    <stop offset="95%" stopColor="#8B5CF6" stopOpacity={0.3}/>
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#F3F4F6" />
                <XAxis dataKey="hour" axisLine={false} tickLine={false} tick={{fill: '#9CA3AF', fontSize: 10, fontWeight: 'bold'}} />
                <YAxis axisLine={false} tickLine={false} tick={{fill: '#9CA3AF', fontSize: 11, fontWeight: 'bold'}} />
                <Tooltip contentStyle={{borderRadius: '16px', border: 'none', boxShadow: '0 10px 15px -3px rgb(0 0 0 / 0.1)'}} />
                <Bar dataKey="count" fill="url(#colorHour)" radius={[6, 6, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

      </div>

    </div>
  );
};
