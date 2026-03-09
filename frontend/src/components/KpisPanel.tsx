import { useEffect, useState } from 'react';
import { api } from '../services/api';
import { TrendingUp, TrendingDown, Users, MessageSquare, Star, AlertTriangle, ArrowRightLeft, Package } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { Separator } from '@/components/ui/separator';
import { cn } from '@/lib/utils';

interface MethodologyItem {
  formula: string;
  description: string;
  numerator: number;
  denominator: number;
  result: number;
  unit: string;
}

interface Metric {
  id: string;
  label: string;
  count: number;
  pct: number;
  base_label: string;
  explanation: string;
  color: string;
}

interface WasteCategory {
  category: string;
  count: number;
  pct_of_waste: number;
}

interface KpisDetailedData {
  kpis: Record<string, number>;
  funnel: {
    metrics: Metric[];
    waste_by_category: WasteCategory[];
  };
  surveys: {
    stats: { total: number; useful: number; not_useful: number };
  };
  methodology: Record<string, MethodologyItem>;
}

interface Props {
  startDate?: string;
  endDate?: string;
}

const METHODOLOGY_CONFIG = [
  {
    key: 'greeting_rate',
    label: 'Tasa Solo Saludo',
    icon: TrendingDown,
    cardClass: 'border-amber-200 bg-amber-50/50',
    iconClass: 'text-amber-500',
    badgeVariant: 'warning' as const,
    progressClass: 'bg-amber-400',
  },
  {
    key: 'self_service',
    label: 'Auto-Servicio',
    icon: TrendingUp,
    cardClass: 'border-green-200 bg-green-50/50',
    iconClass: 'text-green-600',
    badgeVariant: 'success' as const,
    progressClass: 'bg-green-400',
  },
  {
    key: 'utility_index',
    label: 'Índice de Utilidad',
    icon: Star,
    cardClass: 'border-blue-200 bg-blue-50/50',
    iconClass: 'text-blue-600',
    badgeVariant: 'primary' as const,
    progressClass: 'bg-blue-400',
  },
  {
    key: 'failure_rate',
    label: 'Tasa de Fallos IA',
    icon: AlertTriangle,
    cardClass: 'border-red-200 bg-red-50/50',
    iconClass: 'text-red-500',
    badgeVariant: 'danger' as const,
    progressClass: 'bg-red-400',
  },
  {
    key: 'referral_failure',
    label: 'Redirección por Fallo',
    icon: ArrowRightLeft,
    cardClass: 'border-orange-200 bg-orange-50/50',
    iconClass: 'text-orange-500',
    badgeVariant: 'orange' as const,
    progressClass: 'bg-orange-400',
  },
  {
    key: 'value_waste',
    label: 'Gasto de Valor',
    icon: AlertTriangle,
    cardClass: 'border-rose-200 bg-rose-50/50',
    iconClass: 'text-rose-500',
    badgeVariant: 'danger' as const,
    progressClass: 'bg-rose-400',
  },
];

function N(n: number | undefined): string {
  if (n === undefined || n === null) return '—';
  return Math.round(n).toLocaleString('es-CO');
}

function SectionHeader({ icon: Icon, iconClass, title }: { icon: React.ElementType; iconClass?: string; title: string }) {
  return (
    <div className="flex items-center gap-2 mb-4">
      <Icon size={18} className={cn('shrink-0', iconClass ?? 'text-blue-600')} />
      <h2 className="text-base font-semibold text-gray-800">{title}</h2>
    </div>
  );
}

export function KpisPanel({ startDate, endDate }: Props) {
  const [data, setData] = useState<KpisDetailedData | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true);
    api.getKpisDetailed({ start_date: startDate, end_date: endDate })
      .then(setData)
      .catch(console.error)
      .finally(() => setLoading(false));
  }, [startDate, endDate]);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64 text-gray-400 text-sm">
        Cargando KPIs...
      </div>
    );
  }

  if (!data) return null;

  const waste = data.funnel?.waste_by_category ?? [];
  const surveyStats = data.surveys?.stats ?? { total: 0, useful: 0, not_useful: 0 };
  const methodology = data.methodology ?? {};
  const kpis = data.kpis ?? {};
  const metrics = data.funnel?.metrics ?? [];

  // Build metric lookup for product vs general section
  const metricsMap: Record<string, Metric> = {};
  for (const m of metrics) {
    metricsMap[m.id] = m;
  }

  const withProduct = metricsMap['with_product'];
  const general = metricsMap['general'];
  const active = metricsMap['active'];

  const usefulPct = surveyStats.total ? (surveyStats.useful / surveyStats.total) * 100 : 0;
  const notUsefulPct = surveyStats.total ? (surveyStats.not_useful / surveyStats.total) * 100 : 0;

  return (
    <div className="space-y-8">

      {/* ── Methodology ── */}
      <section>
        <SectionHeader icon={Star} iconClass="text-yellow-500" title="Metodología — Cómo se Calcula Cada KPI" />
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {METHODOLOGY_CONFIG.map(({ key, label, cardClass, iconClass, badgeVariant, progressClass, icon: Icon }) => {
            const m = methodology[key];
            if (!m) return null;
            return (
              <Card key={key} className={cn('border', cardClass)}>
                <CardHeader className="pb-2">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <Icon size={18} className={iconClass} />
                      <CardTitle className="text-sm">{label}</CardTitle>
                    </div>
                    <Badge variant={badgeVariant} className="text-base px-3 py-1 rounded-lg font-bold">
                      {m.result.toFixed(1)}{m.unit}
                    </Badge>
                  </div>
                </CardHeader>
                <CardContent className="pt-0 space-y-3">
                  <p className="text-xs text-gray-600">{m.description}</p>

                  {/* Progress bar */}
                  <Progress
                    value={Math.min(m.result, 100)}
                    className="h-1.5 bg-white/60"
                    indicatorClassName={progressClass}
                  />

                  {/* Formula */}
                  <div className="bg-white/70 rounded-lg px-3 py-2 text-xs font-mono text-gray-700 border border-white/80">
                    {m.formula}
                  </div>

                  <div className="flex gap-4 text-xs text-gray-500">
                    <span>Numerador: <strong className="text-gray-700">{N(m.numerator)}</strong></span>
                    <span>Denominador: <strong className="text-gray-700">{N(m.denominator)}</strong></span>
                  </div>
                </CardContent>
              </Card>
            );
          })}
        </div>
      </section>

      {/* ── Operational KPIs ── */}
      <section>
        <SectionHeader icon={MessageSquare} title="KPIs Operacionales" />
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
          {[
            { label: 'Conversaciones', value: N(kpis.total_conversations), icon: MessageSquare, color: 'text-blue-600' },
            { label: 'Usuarios únicos', value: N(kpis.total_users), icon: Users, color: 'text-violet-600' },
            { label: 'Msgs promedio / conv', value: (kpis.avg_messages_per_thread ?? 0).toFixed(2), icon: MessageSquare, color: 'text-teal-600' },
            { label: 'Tokens de entrada', value: N(kpis.total_input_tokens), icon: TrendingUp, color: 'text-amber-600' },
          ].map((item, i) => (
            <Card key={i}>
              <CardContent className="pt-4 pb-4">
                <div className="flex items-center gap-2 mb-2">
                  <item.icon size={14} className={item.color} />
                  <span className="text-xs text-gray-500">{item.label}</span>
                </div>
                <div className="text-xl font-bold text-gray-900 tabular-nums">{item.value}</div>
              </CardContent>
            </Card>
          ))}
        </div>
      </section>

      {/* ── Product vs General ── */}
      {withProduct && general && active && (
        <section>
          <SectionHeader icon={Package} iconClass="text-teal-600" title="Producto vs Consultas Generales" />
          <p className="text-xs text-gray-500 mb-3 -mt-2">
            De las {N(active.count)} conversaciones activas, cuántas mencionan un producto bancario específico.
          </p>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <Card className="border-emerald-200 bg-emerald-50/40">
              <CardContent className="pt-5 pb-4 space-y-2">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-semibold text-emerald-700 uppercase tracking-wider">Sobre un Producto</span>
                  <Badge variant="success">{withProduct.pct}%</Badge>
                </div>
                <div className="text-3xl font-bold text-emerald-800 tabular-nums">{N(withProduct.count)}</div>
                <Progress value={withProduct.pct} className="h-1.5 bg-emerald-100" indicatorClassName="bg-emerald-500" />
                <p className="text-xs text-emerald-600">{withProduct.explanation}</p>
              </CardContent>
            </Card>
            <Card className="border-gray-200 bg-gray-50/40">
              <CardContent className="pt-5 pb-4 space-y-2">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-semibold text-gray-600 uppercase tracking-wider">Consultas Generales</span>
                  <Badge variant="default">{general.pct}%</Badge>
                </div>
                <div className="text-3xl font-bold text-gray-800 tabular-nums">{N(general.count)}</div>
                <Progress value={general.pct} className="h-1.5 bg-gray-200" indicatorClassName="bg-gray-400" />
                <p className="text-xs text-gray-500">{general.explanation}</p>
              </CardContent>
            </Card>
          </div>
        </section>
      )}

      {/* ── Value Waste ── */}
      {waste.length > 0 && (
        <section>
          <SectionHeader icon={AlertTriangle} iconClass="text-rose-500" title="Gasto de Valor por Categoría" />
          <p className="text-xs text-gray-500 mb-3 -mt-2">
            Conversaciones que recibieron «No me fue útil» y además fueron derivadas a un canal externo.
          </p>
          <Card className="overflow-hidden">
            <table className="w-full text-sm">
              <thead>
                <tr className="bg-gray-50 border-b border-gray-100">
                  <th className="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">Categoría</th>
                  <th className="px-4 py-3 text-right text-xs font-semibold text-gray-500 uppercase tracking-wider">Conversaciones</th>
                  <th className="px-4 py-3 text-right text-xs font-semibold text-gray-500 uppercase tracking-wider">% del gasto</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-50">
                {waste.map((w, i) => (
                  <tr key={i} className="hover:bg-gray-50 transition-colors">
                    <td className="px-4 py-3 text-gray-700">{w.category}</td>
                    <td className="px-4 py-3 text-right">
                      <Badge variant="danger">{N(w.count)}</Badge>
                    </td>
                    <td className="px-4 py-3 text-right text-gray-500 text-xs">{w.pct_of_waste.toFixed(1)}%</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </Card>
        </section>
      )}

      {/* ── Surveys ── */}
      <section>
        <SectionHeader icon={Star} iconClass="text-yellow-500" title="Encuestas de Satisfacción" />
        <div className="grid grid-cols-1 md:grid-cols-3 gap-3 mb-4">
          <Card className="text-center">
            <CardContent className="pt-5">
              <div className="text-3xl font-bold text-gray-900 tabular-nums">{N(surveyStats.total)}</div>
              <div className="text-xs text-gray-500 mt-1">Total respondidas</div>
            </CardContent>
          </Card>
          <Card className="text-center border-green-200 bg-green-50/40">
            <CardContent className="pt-5 space-y-2">
              <div className="text-3xl font-bold text-green-700 tabular-nums">{N(surveyStats.useful)}</div>
              <div className="text-xs text-green-600">«Me fue útil» ({usefulPct.toFixed(1)}%)</div>
              <Progress value={usefulPct} className="h-1.5 bg-green-100" indicatorClassName="bg-green-500" />
            </CardContent>
          </Card>
          <Card className="text-center border-rose-200 bg-rose-50/40">
            <CardContent className="pt-5 space-y-2">
              <div className="text-3xl font-bold text-rose-700 tabular-nums">{N(surveyStats.not_useful)}</div>
              <div className="text-xs text-rose-600">«No me fue útil» ({notUsefulPct.toFixed(1)}%)</div>
              <Progress value={notUsefulPct} className="h-1.5 bg-rose-100" indicatorClassName="bg-rose-500" />
            </CardContent>
          </Card>
        </div>

        {/* Combined bar */}
        {surveyStats.total > 0 && (
          <Card>
            <CardContent className="pt-4 pb-4">
              <div className="text-xs text-gray-500 mb-2 font-medium">Distribución de satisfacción</div>
              <div className="flex h-3 rounded-full overflow-hidden gap-px">
                <div
                  className="bg-green-400 transition-all"
                  style={{ width: `${usefulPct}%` }}
                  title={`Útil: ${usefulPct.toFixed(1)}%`}
                />
                <div
                  className="bg-rose-400 transition-all"
                  style={{ width: `${notUsefulPct}%` }}
                  title={`No útil: ${notUsefulPct.toFixed(1)}%`}
                />
              </div>
              <div className="flex justify-between mt-2">
                <span className="text-xs text-green-600 font-medium">{usefulPct.toFixed(1)}% útiles</span>
                <span className="text-xs text-rose-600 font-medium">{notUsefulPct.toFixed(1)}% no útiles</span>
              </div>
            </CardContent>
          </Card>
        )}
        <Separator className="mt-4" />
      </section>

    </div>
  );
}
