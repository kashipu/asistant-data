import { useEffect, useState } from 'react';
import { api } from '../services/api';
import { AlertOctagon, Bot, ChevronLeft, ChevronRight, ExternalLink, Package, PhoneCall, Search } from 'lucide-react';
import { Card, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { Separator } from '@/components/ui/separator';
import {
  Accordion,
  AccordionItem,
  AccordionTrigger,
  AccordionContent,
} from '@/components/ui/accordion';
import { cn } from '@/lib/utils';

interface FailureExample {
  thread_id: string;
  fecha: string;
  last_user_message: string;
  last_ai_message?: string;
  criteria: string;
  sentiment: string;
  product?: string;
}

interface TopProduct {
  name: string;
  count: number;
}

interface AiResponse {
  text: string;
  count: number;
}

interface FailureCategory {
  category: string;
  count: number;
  pct: number;
  criteria_breakdown: Record<string, number>;
  top_products?: TopProduct[];
  top_ai_responses?: AiResponse[];
  redirected_count?: number;
  redirected_pct?: number;
  examples: FailureExample[];
}

interface FailuresDetailedData {
  total: number;
  total_conversations: number;
  criteria_global?: Record<string, number>;
  by_category: FailureCategory[];
}

interface Props {
  onNavigateToThread?: (threadId: string) => void;
  startDate?: string;
  endDate?: string;
}

const CRITERIA_COLORS: Record<string, { bg: string; text: string; badge: 'warning' | 'primary' | 'danger' }> = {
  'Respuesta de incapacidad del bot': { bg: 'bg-amber-100', text: 'text-amber-800', badge: 'warning' },
  'Usuario repite pregunta': { bg: 'bg-blue-100', text: 'text-blue-800', badge: 'primary' },
  'Sentimiento negativo predominante': { bg: 'bg-rose-100', text: 'text-rose-800', badge: 'danger' },
};

function N(n: number): string {
  return Math.round(n).toLocaleString('es-CO');
}

function CriteriaChip({ crit, count }: { crit: string; count?: number }) {
  const colors = CRITERIA_COLORS[crit];
  const variant = colors?.badge ?? 'default';
  return (
    <Badge variant={variant} className="text-[10px] px-1.5 py-0.5 rounded gap-1">
      {count !== undefined && <strong>{count}</strong>}
      {crit}
    </Badge>
  );
}

const PAGE_SIZE = 15;

function FailureExamplesTable({
  examples,
  onNavigateToThread,
}: {
  examples: FailureExample[];
  onNavigateToThread?: (threadId: string) => void;
}) {
  const [page, setPage] = useState(1);
  const totalPages = Math.ceil(examples.length / PAGE_SIZE);
  const paged = examples.slice((page - 1) * PAGE_SIZE, page * PAGE_SIZE);

  return (
    <div>
      <div className="flex items-center justify-between mb-3">
        <div className="text-xs font-semibold text-gray-500 uppercase tracking-wider">
          Todas las conversaciones fallidas
          <span className="ml-2 text-gray-400 normal-case font-normal">({N(examples.length)})</span>
        </div>
        {totalPages > 1 && (
          <div className="flex items-center gap-2 text-xs">
            <button
              onClick={() => setPage(p => Math.max(1, p - 1))}
              disabled={page <= 1}
              className="p-1 rounded hover:bg-gray-200 disabled:opacity-30"
            >
              <ChevronLeft size={14} />
            </button>
            <span className="text-gray-500 tabular-nums">{page}/{totalPages}</span>
            <button
              onClick={() => setPage(p => Math.min(totalPages, p + 1))}
              disabled={page >= totalPages}
              className="p-1 rounded hover:bg-gray-200 disabled:opacity-30"
            >
              <ChevronRight size={14} />
            </button>
          </div>
        )}
      </div>
      <div className="overflow-x-auto rounded-lg border border-gray-100">
        <table className="w-full text-xs">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-3 py-2.5 text-left text-gray-400 font-semibold uppercase tracking-wider">Fecha</th>
              <th className="px-3 py-2.5 text-left text-gray-400 font-semibold uppercase tracking-wider">Producto</th>
              <th className="px-3 py-2.5 text-left text-gray-400 font-semibold uppercase tracking-wider">Usuario pregunta</th>
              <th className="px-3 py-2.5 text-left text-gray-400 font-semibold uppercase tracking-wider">IA responde</th>
              <th className="px-3 py-2.5 text-left text-gray-400 font-semibold uppercase tracking-wider">Criterio</th>
              <th className="px-3 py-2.5 text-left text-gray-400 font-semibold uppercase tracking-wider">Thread</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-50">
            {paged.map((ex, i) => (
              <tr key={i} className="hover:bg-gray-50 transition-colors">
                <td className="px-3 py-2.5 text-gray-400 whitespace-nowrap">{ex.fecha}</td>
                <td className="px-3 py-2.5">
                  {ex.product ? (
                    <Badge variant="teal" className="text-[10px]">{ex.product}</Badge>
                  ) : (
                    <span className="text-gray-300">-</span>
                  )}
                </td>
                <td className="px-3 py-2.5 text-gray-700 max-w-[200px]">
                  <span className="line-clamp-2">{ex.last_user_message}</span>
                </td>
                <td className="px-3 py-2.5 text-gray-500 max-w-[250px]">
                  {ex.last_ai_message ? (
                    <span className="line-clamp-2 text-[11px] italic">{ex.last_ai_message}</span>
                  ) : (
                    <span className="text-gray-300">-</span>
                  )}
                </td>
                <td className="px-3 py-2.5">
                  <div className="flex flex-wrap gap-1">
                    {ex.criteria.split(',').map((c, ci) => (
                      <CriteriaChip key={ci} crit={c.trim()} />
                    ))}
                  </div>
                </td>
                <td className="px-3 py-2.5">
                  {onNavigateToThread ? (
                    <button
                      onClick={() => onNavigateToThread(ex.thread_id)}
                      className="flex items-center gap-1 font-mono text-blue-600 hover:text-blue-800 transition-colors"
                    >
                      <ExternalLink size={10} />
                      {ex.thread_id.slice(0, 12)}
                    </button>
                  ) : (
                    <span className="font-mono text-gray-400">{ex.thread_id.slice(0, 12)}</span>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

export function FailuresDeepPanel({ onNavigateToThread, startDate, endDate }: Props) {
  const [data, setData] = useState<FailuresDetailedData | null>(null);
  const [loading, setLoading] = useState(true);
  const [openCat, setOpenCat] = useState<string>('');
  const [search, setSearch] = useState('');

  useEffect(() => {
    api.getFailuresDetailed({ start_date: startDate, end_date: endDate })
      .then((d: FailuresDetailedData) => {
        setData(d);
        if (d.by_category?.length > 0) setOpenCat(d.by_category[0].category);
      })
      .catch(console.error)
      .finally(() => setLoading(false));
  }, [startDate, endDate]);

  if (loading) {
    return <div className="flex items-center justify-center h-64 text-gray-400 text-sm">Cargando fallos...</div>;
  }

  if (!data) return null;

  const filteredCats = search.trim()
    ? data.by_category.filter(c => c.category.toLowerCase().includes(search.toLowerCase()))
    : data.by_category;

  const failPct = data.total_conversations
    ? (data.total / data.total_conversations) * 100
    : 0;

  const criteriaGlobal = data.criteria_global || {};
  const totalCriteriaHits = Object.values(criteriaGlobal).reduce((a, b) => a + b, 0);

  return (
    <div className="space-y-5">

      {/* Header summary */}
      <Card className="border-rose-200 bg-rose-50/50">
        <CardContent className="pt-5 pb-4">
          <div className="flex items-center gap-4">
            <AlertOctagon className="text-rose-500 shrink-0" size={36} />
            <div className="flex-1 min-w-0">
              <div className="text-2xl font-bold text-rose-700 tabular-nums">{N(data.total)} conversaciones con fallo</div>
              <div className="text-sm text-rose-600 mt-0.5">
                <strong>{failPct.toFixed(1)}%</strong> de {N(data.total_conversations)} conversaciones totales
              </div>
              <Progress
                value={failPct}
                className="mt-3 h-1.5 bg-rose-100"
                indicatorClassName="bg-rose-400"
              />
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Global criteria breakdown */}
      {totalCriteriaHits > 0 && (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
          {Object.entries(criteriaGlobal).sort((a, b) => b[1] - a[1]).map(([crit, cnt]) => {
            const colors = CRITERIA_COLORS[crit] || { bg: 'bg-gray-100', text: 'text-gray-700' };
            const pctOfTotal = data.total_conversations > 0 ? (cnt / data.total_conversations * 100).toFixed(1) : '0';
            return (
              <div key={crit} className={cn('rounded-xl p-4 border', colors.bg, 'border-opacity-50')}>
                <div className={cn('text-[10px] font-semibold uppercase tracking-wider mb-1', colors.text)}>{crit}</div>
                <div className={cn('text-2xl font-bold tabular-nums', colors.text)}>{N(cnt)}</div>
                <div className="text-xs text-gray-500 mt-1">{pctOfTotal}% de {N(data.total_conversations)} conversaciones</div>
              </div>
            );
          })}
        </div>
      )}

      <Separator />

      {/* Search */}
      <div className="relative">
        <Search size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
        <input
          type="text"
          value={search}
          onChange={e => setSearch(e.target.value)}
          placeholder="Buscar por categoria..."
          className="w-full border border-gray-200 rounded-lg pl-9 pr-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-rose-300 bg-white"
        />
      </div>

      {/* Category accordion */}
      <Accordion
        type="single"
        collapsible
        value={openCat}
        onValueChange={setOpenCat}
        className="space-y-3"
      >
        {filteredCats.map(cat => (
          <AccordionItem
            key={cat.category}
            value={cat.category}
            className="bg-white rounded-xl border border-gray-200 shadow-sm overflow-hidden"
          >
            <AccordionTrigger className="px-5 py-4 hover:bg-gray-50 rounded-none">
              <div className="flex items-center gap-2 flex-wrap">
                <span className="font-semibold text-gray-800">{cat.category || 'Sin categoria'}</span>
                <Badge variant="danger">{N(cat.count)} fallos</Badge>
                <span className="text-xs text-gray-400">{cat.pct.toFixed(1)}%</span>
                {(cat.redirected_pct ?? 0) > 0 && (
                  <Badge variant="orange" className="text-[10px]">
                    <PhoneCall size={9} className="mr-0.5" />
                    {cat.redirected_pct}% redir.
                  </Badge>
                )}
                {cat.top_products && cat.top_products.length > 0 && (
                  <Badge variant="teal" className="text-[10px]">
                    <Package size={9} className="mr-0.5" />
                    {cat.top_products[0].name}
                  </Badge>
                )}
              </div>
            </AccordionTrigger>

            <AccordionContent className="p-0 pb-0">
              <Separator />
              <div className="p-5 space-y-5">

                {/* Row 1: Criteria + Products + Correlations */}
                <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
                  {/* Criteria breakdown */}
                  <div>
                    <div className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-3">
                      Criterios de fallo
                    </div>
                    <div className="space-y-2">
                      {Object.entries(cat.criteria_breakdown).map(([crit, cnt]) => {
                        const colors = CRITERIA_COLORS[crit] || { bg: 'bg-gray-100', text: 'text-gray-700' };
                        return (
                          <div
                            key={crit}
                            className={cn(
                              'flex items-center gap-1.5 text-xs px-2.5 py-1.5 rounded-lg',
                              colors.bg, colors.text
                            )}
                          >
                            <strong className="tabular-nums">{cnt as number}</strong>
                            <span>— {crit}</span>
                          </div>
                        );
                      })}
                    </div>
                    {/* Redirection correlation */}
                    {(cat.redirected_count ?? 0) > 0 && (
                      <div className="mt-3 flex items-center gap-1.5 text-xs text-orange-700 bg-orange-50 px-2.5 py-1.5 rounded-lg">
                        <PhoneCall size={10} />
                        <span><strong>{N(cat.redirected_count ?? 0)}</strong> redirigidas ({cat.redirected_pct}%)</span>
                      </div>
                    )}
                  </div>

                  {/* Products associated */}
                  {cat.top_products && cat.top_products.length > 0 && (
                    <div>
                      <div className="flex items-center gap-1.5 text-xs font-semibold text-gray-500 uppercase tracking-wider mb-3">
                        <Package size={11} />
                        Productos afectados
                      </div>
                      <div className="space-y-1.5">
                        {cat.top_products.map((p, i) => (
                          <div key={i} className="flex items-center justify-between text-xs">
                            <span className="text-gray-700">{p.name}</span>
                            <span className="font-semibold text-gray-800 tabular-nums">{N(p.count)}</span>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* AI Responses — what the bot says when it fails */}
                  {cat.top_ai_responses && cat.top_ai_responses.length > 0 && (
                    <div>
                      <div className="flex items-center gap-1.5 text-xs font-semibold text-gray-500 uppercase tracking-wider mb-3">
                        <Bot size={11} />
                        Que responde la IA
                      </div>
                      <div className="space-y-2">
                        {cat.top_ai_responses.map((r, i) => (
                          <div key={i} className="bg-gray-50 border border-gray-100 rounded-lg p-2.5">
                            <div className="text-[10px] text-gray-500 line-clamp-3 leading-relaxed">
                              "{r.text}..."
                            </div>
                            <div className="text-[10px] font-semibold text-gray-400 mt-1">{r.count}x</div>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </div>

                {/* Examples table with pagination */}
                <FailureExamplesTable
                  examples={cat.examples}
                  onNavigateToThread={onNavigateToThread}
                />

              </div>
            </AccordionContent>
          </AccordionItem>
        ))}
      </Accordion>

      {filteredCats.length === 0 && (
        <div className="text-center py-12 text-gray-400 text-sm">
          No se encontraron categorias con ese filtro.
        </div>
      )}
    </div>
  );
}
