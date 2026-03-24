import { useEffect, useState } from 'react';
import { api } from '../services/api';
import { Loader2, AlertCircle, UserCheck, PhoneForwarded, BugPlay, TrendingUp, Users, Headphones } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from './ui/card';
import { Badge } from './ui/badge';
import { Progress } from './ui/progress';

interface EscalationData {
  total_conversations: number;
  arrived_seeking_advisor: number;
  arrived_seeking_pct: number;
  total_redirected: number;
  total_redirected_pct: number;
  by_channel: Record<string, number>;
  arrived_and_redirected: number;
  organic_escalation: number;
  organic_escalation_pct: number;
  bot_failed_then_redirected: number;
  bot_failed_then_redirected_pct: number;
  top_categories_organic: { name: string; conversations: number; pct: number }[];
  top_subcategories_organic: { name: string; conversations: number; pct: number }[];
}

interface AdvisorPanelProps {
  startDate?: string;
  endDate?: string;
}

const N = (n: number) => n.toLocaleString('es-CO');

const channelLabels: Record<string, string> = {
  digital: 'Canal Digital',
  serviline: 'Servilinea',
  office: 'Oficina',
};

const channelColors: Record<string, string> = {
  digital: 'bg-blue-500',
  serviline: 'bg-violet-500',
  office: 'bg-amber-500',
};

export function AdvisorPanel({ startDate, endDate }: AdvisorPanelProps) {
  const [data, setData] = useState<EscalationData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const load = async () => {
      setLoading(true);
      setError(null);
      try {
        const result = await api.getAdvisorEscalation(startDate, endDate);
        setData(result);
      } catch (_err) {
        setError("Error cargando datos de escalamiento.");
      } finally {
        setLoading(false);
      }
    };
    load();
  }, [startDate, endDate]);

  if (loading) {
    return (
      <div className="p-12 text-center text-gray-400">
        <Loader2 className="w-8 h-8 animate-spin mx-auto mb-3" />
        Cargando metricas de escalamiento...
      </div>
    );
  }

  if (error || !data) {
    return (
      <div className="p-8 text-center text-red-500">
        <AlertCircle size={32} className="mx-auto mb-2" />
        <p>{error}</p>
      </div>
    );
  }

  const totalRedirected = data.total_redirected;
  const channelEntries = Object.entries(data.by_channel).sort(([, a], [, b]) => b - a);

  return (
    <div className="space-y-6">
      {/* Main KPI Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <Card className="border-l-4 border-l-violet-500">
          <CardContent className="pt-5 pb-4">
            <div className="flex items-start justify-between">
              <div>
                <p className="text-xs font-medium text-gray-500 uppercase tracking-wider">Llegaron buscando asesor</p>
                <h3 className="text-3xl font-bold text-gray-900 mt-1">{N(data.arrived_seeking_advisor)}</h3>
                <p className="text-sm text-violet-600 font-medium mt-1">{data.arrived_seeking_pct}% del total</p>
              </div>
              <div className="p-2.5 rounded-lg bg-violet-100 text-violet-600">
                <UserCheck className="w-5 h-5" />
              </div>
            </div>
            <p className="text-[11px] text-gray-400 mt-3">Su primera intencion fue hablar con un asesor humano</p>
          </CardContent>
        </Card>

        <Card className="border-l-4 border-l-blue-500">
          <CardContent className="pt-5 pb-4">
            <div className="flex items-start justify-between">
              <div>
                <p className="text-xs font-medium text-gray-500 uppercase tracking-wider">Terminaron redirigidos</p>
                <h3 className="text-3xl font-bold text-gray-900 mt-1">{N(data.total_redirected)}</h3>
                <p className="text-sm text-blue-600 font-medium mt-1">{data.total_redirected_pct}% del total</p>
              </div>
              <div className="p-2.5 rounded-lg bg-blue-100 text-blue-600">
                <PhoneForwarded className="w-5 h-5" />
              </div>
            </div>
            <p className="text-[11px] text-gray-400 mt-3">Fueron derivados a algun canal de atencion</p>
          </CardContent>
        </Card>

        <Card className="border-l-4 border-l-orange-500">
          <CardContent className="pt-5 pb-4">
            <div className="flex items-start justify-between">
              <div>
                <p className="text-xs font-medium text-gray-500 uppercase tracking-wider">Bot fallo y redirigidos</p>
                <h3 className="text-3xl font-bold text-gray-900 mt-1">{N(data.bot_failed_then_redirected)}</h3>
                <p className="text-sm text-orange-600 font-medium mt-1">{data.bot_failed_then_redirected_pct}% del total</p>
              </div>
              <div className="p-2.5 rounded-lg bg-orange-100 text-orange-600">
                <BugPlay className="w-5 h-5" />
              </div>
            </div>
            <p className="text-[11px] text-gray-400 mt-3">El bot no resolvio y el usuario fue derivado</p>
          </CardContent>
        </Card>

        <Card className="border-l-4 border-l-teal-500">
          <CardContent className="pt-5 pb-4">
            <div className="flex items-start justify-between">
              <div>
                <p className="text-xs font-medium text-gray-500 uppercase tracking-wider">Escalamiento organico</p>
                <h3 className="text-3xl font-bold text-gray-900 mt-1">{N(data.organic_escalation)}</h3>
                <p className="text-sm text-teal-600 font-medium mt-1">{data.organic_escalation_pct}% del total</p>
              </div>
              <div className="p-2.5 rounded-lg bg-teal-100 text-teal-600">
                <TrendingUp className="w-5 h-5" />
              </div>
            </div>
            <p className="text-[11px] text-gray-400 mt-3">No buscaban asesor pero terminaron siendo redirigidos</p>
          </CardContent>
        </Card>
      </div>

      {/* Funnel visual */}
      <Card>
        <CardHeader className="pb-3">
          <CardTitle className="text-base font-semibold flex items-center gap-2">
            <Users className="w-4 h-4 text-gray-500" />
            Embudo de Escalamiento
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {/* Total */}
            <div>
              <div className="flex justify-between text-sm mb-1">
                <span className="text-gray-600">Total conversaciones</span>
                <span className="font-semibold">{N(data.total_conversations)}</span>
              </div>
              <Progress value={100} className="h-3" indicatorClassName="bg-gray-300" />
            </div>
            {/* Redirected */}
            <div>
              <div className="flex justify-between text-sm mb-1">
                <span className="text-gray-600">Redirigidos a algun canal</span>
                <span className="font-semibold">{N(data.total_redirected)} <span className="text-gray-400 font-normal">({data.total_redirected_pct}%)</span></span>
              </div>
              <Progress value={data.total_redirected_pct} className="h-3" indicatorClassName="bg-blue-400" />
            </div>
            {/* Organic */}
            <div>
              <div className="flex justify-between text-sm mb-1">
                <span className="text-gray-600">No buscaban asesor pero fueron redirigidos</span>
                <span className="font-semibold">{N(data.organic_escalation)} <span className="text-gray-400 font-normal">({data.organic_escalation_pct}%)</span></span>
              </div>
              <Progress value={data.organic_escalation_pct} className="h-3" indicatorClassName="bg-teal-400" />
            </div>
            {/* Arrived seeking */}
            <div>
              <div className="flex justify-between text-sm mb-1">
                <span className="text-gray-600">Llegaron buscando asesor directamente</span>
                <span className="font-semibold">{N(data.arrived_seeking_advisor)} <span className="text-gray-400 font-normal">({data.arrived_seeking_pct}%)</span></span>
              </div>
              <Progress value={data.arrived_seeking_pct} className="h-3" indicatorClassName="bg-violet-400" />
            </div>
            {/* Bot failed */}
            <div>
              <div className="flex justify-between text-sm mb-1">
                <span className="text-gray-600">Bot fallo y fueron redirigidos</span>
                <span className="font-semibold">{N(data.bot_failed_then_redirected)} <span className="text-gray-400 font-normal">({data.bot_failed_then_redirected_pct}%)</span></span>
              </div>
              <Progress value={data.bot_failed_then_redirected_pct} className="h-3" indicatorClassName="bg-orange-400" />
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Two-column: channels + categories */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Channels */}
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-base font-semibold flex items-center gap-2">
              <Headphones className="w-4 h-4 text-gray-500" />
              Canales de Redireccion
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {channelEntries.map(([channel, count]) => (
                <div key={channel}>
                  <div className="flex justify-between text-sm mb-1">
                    <span className="text-gray-700 font-medium">{channelLabels[channel] || channel}</span>
                    <span className="text-gray-500">{N(count)} <span className="text-gray-400">({totalRedirected ? ((count / totalRedirected) * 100).toFixed(1) : 0}%)</span></span>
                  </div>
                  <div className="w-full bg-gray-100 rounded-full h-2.5">
                    <div
                      className={`h-2.5 rounded-full ${channelColors[channel] || 'bg-gray-400'}`}
                      style={{ width: `${totalRedirected ? (count / totalRedirected) * 100 : 0}%` }}
                    />
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        {/* Top categories that ended requesting (organic) */}
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-base font-semibold">
              De que hablaban los que terminaron pidiendo asesor?
            </CardTitle>
            <p className="text-xs text-gray-400 mt-1">Categorias de usuarios que no buscaban asesor pero fueron redirigidos</p>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              {data.top_categories_organic.map((cat, i) => (
                <div key={cat.name} className="flex items-center justify-between py-1.5 border-b border-gray-50 last:border-0">
                  <div className="flex items-center gap-2">
                    <span className="text-xs text-gray-400 w-4 text-right">{i + 1}</span>
                    <span className="text-sm text-gray-700">{cat.name}</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className="text-sm font-medium text-gray-900">{N(cat.conversations)}</span>
                    <Badge variant="outline" className="text-[10px]">{cat.pct}%</Badge>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Subcategories detail */}
      <Card>
        <CardHeader className="pb-3">
          <CardTitle className="text-base font-semibold">
            Subcategorias con mayor escalamiento organico
          </CardTitle>
          <p className="text-xs text-gray-400 mt-1">Temas especificos donde el bot no logro resolver y el usuario fue derivado</p>
        </CardHeader>
        <CardContent>
          <div className="overflow-x-auto">
            <table className="w-full text-left">
              <thead className="bg-gray-50 border-b border-gray-200">
                <tr>
                  <th className="px-4 py-2.5 text-xs font-medium text-gray-500 uppercase tracking-wider">#</th>
                  <th className="px-4 py-2.5 text-xs font-medium text-gray-500 uppercase tracking-wider">Subcategoria</th>
                  <th className="px-4 py-2.5 text-xs font-medium text-gray-500 uppercase tracking-wider text-right">Conversaciones</th>
                  <th className="px-4 py-2.5 text-xs font-medium text-gray-500 uppercase tracking-wider text-right">% del organico</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-50">
                {data.top_subcategories_organic.map((sub, i) => (
                  <tr key={sub.name} className="hover:bg-gray-50">
                    <td className="px-4 py-2.5 text-xs text-gray-400">{i + 1}</td>
                    <td className="px-4 py-2.5 text-sm text-gray-700">{sub.name}</td>
                    <td className="px-4 py-2.5 text-sm font-medium text-gray-900 text-right">{N(sub.conversations)}</td>
                    <td className="px-4 py-2.5 text-right">
                      <Badge variant={sub.pct > 10 ? "warning" : "outline"} className="text-[10px]">{sub.pct}%</Badge>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
