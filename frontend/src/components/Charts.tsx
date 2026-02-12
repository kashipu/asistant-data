
import { useEffect, useState } from 'react';
import { api } from '../services/api';
import { 
  LineChart, Line, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, PieChart, Pie, Cell 
} from 'recharts';
import { Loader2 } from 'lucide-react';

const COLORS = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042', '#8884d8', '#82ca9d'];


interface ChartsProps {
  startDate?: string;
  endDate?: string;
}

export const Charts = ({ startDate, endDate }: ChartsProps) => {
  const [temporalData, setTemporalData] = useState<any>(null);
  const [categoricalData, setCategoricalData] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchData = async () => {
        setLoading(true);
        try {
            // Note: API for analysis currently might not support date filtering yet in backend
            // But we should pass it if we implemented it.
            // Based on previous steps, we haven't explicitly added date filtering to 
            // getTemporalAnalysis and getCategoricalAnalysis in backend/main.py or api.ts
            // Let's check api.ts again.
            // I did NOT update getTemporalAnalysis and getCategoricalAnalysis in api.ts to accept dates.
            // I should assume they will be updated or just pass them for now and update api.ts next.
            // Actually, I'll update api.ts right after this if needed.
            const [temp, cat] = await Promise.all([
                api.getTemporalAnalysis(), // TODO: Add date params
                api.getCategoricalAnalysis() // TODO: Add date params
            ]);
            setTemporalData(temp);
            setCategoricalData(cat);
        } catch (error) {
            console.error(error);
        } finally {
            setLoading(false);
        }
    };
    fetchData();
  }, [startDate, endDate]);

  if (loading || !temporalData || !categoricalData) return (
      <div className="h-64 flex items-center justify-center">
          <Loader2 className="h-8 w-8 animate-spin text-blue-500" />
      </div>
  );

  // Prepare data for Recharts
  const dailyData = Object.entries(temporalData.daily_volume).map(([date, count]) => ({ date, count })).sort((a: any, b: any) => a.date.localeCompare(b.date));
  const hourlyData = Object.entries(temporalData.hourly_volume).map(([hour, count]) => ({ hour: parseInt(hour), count })).sort((a: any, b: any) => a.hour - b.hour);
  
  const intentData = Object.entries(categoricalData.top_intents).map(([name, value]) => ({ name, value })).slice(0, 10);
  const sentimentData = Object.entries(categoricalData.sentiment_distribution).map(([name, value]) => ({ name, value }));

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Daily Volume */}
        <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-100">
            <h3 className="text-lg font-semibold mb-4 text-gray-800">Volumen Diario</h3>
            <div className="h-64">
                <ResponsiveContainer width="100%" height="100%">
                    <LineChart data={dailyData}>
                        <CartesianGrid strokeDasharray="3 3" />
                        <XAxis dataKey="date" />
                        <YAxis />
                        <Tooltip />
                        <Line type="monotone" dataKey="count" stroke="#3B82F6" strokeWidth={2} />
                    </LineChart>
                </ResponsiveContainer>
            </div>
        </div>

        {/* Hourly Volume */}
        <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-100">
            <h3 className="text-lg font-semibold mb-4 text-gray-800">Volumen por Hora</h3>
             <div className="h-64">
                <ResponsiveContainer width="100%" height="100%">
                    <BarChart data={hourlyData}>
                        <CartesianGrid strokeDasharray="3 3" />
                        <XAxis dataKey="hour" />
                        <YAxis />
                        <Tooltip />
                        <Bar dataKey="count" fill="#8884d8" />
                    </BarChart>
                </ResponsiveContainer>
            </div>
        </div>
      </div>

       <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Top Intents */}
        <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-100">
            <h3 className="text-lg font-semibold mb-4 text-gray-800">Top 10 Intenciones</h3>
            <div className="h-80">
                <ResponsiveContainer width="100%" height="100%">
                    <BarChart layout="vertical" data={intentData} margin={{ left: 50 }}>
                        <CartesianGrid strokeDasharray="3 3" />
                        <XAxis type="number" />
                        <YAxis type="category" dataKey="name" width={150} style={{ fontSize: '11px' }} />
                        <Tooltip />
                        <Bar dataKey="value" fill="#82ca9d" />
                    </BarChart>
                </ResponsiveContainer>
            </div>
        </div>

        {/* Sentiment Distribution */}
        <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-100">
            <h3 className="text-lg font-semibold mb-4 text-gray-800">Distribución de Sentimiento</h3>
            <div className="h-64">
                <ResponsiveContainer width="100%" height="100%">
                    <PieChart>
                        <Pie
                            data={sentimentData}
                            cx="50%"
                            cy="50%"
                            labelLine={false}
                            label={({ name, percent }: { name?: string; percent?: number }) => `${name ?? ''} ${((percent ?? 0) * 100).toFixed(0)}%`}
                            outerRadius={80}
                            fill="#8884d8"
                            dataKey="value"
                        >
                            {sentimentData.map((_entry: any, index: number) => (
                            <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                            ))}
                        </Pie>
                        <Tooltip />
                        <Legend />
                    </PieChart>
                </ResponsiveContainer>
            </div>
        </div>
      </div>
    </div>
  );
};
