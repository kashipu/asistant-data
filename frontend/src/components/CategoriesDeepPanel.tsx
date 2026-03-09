import { useEffect, useState, useCallback } from 'react';
import { api } from '../services/api';
import { Layers, Package, MessageSquare, Search, Phone, Monitor, Building2, ArrowRight, ThumbsUp, ThumbsDown, AlertTriangle, ChevronLeft, ChevronRight, ExternalLink } from 'lucide-react';
import { Badge } from '@/components/ui/badge';
import { Separator } from '@/components/ui/separator';
import {
  Accordion,
  AccordionItem,
  AccordionTrigger,
  AccordionContent,
} from '@/components/ui/accordion';
import { cn } from '@/lib/utils';

export interface UserPhrase {
  phrase: string;
  count: number;
}

export interface Product {
  name: string;
  conversations: number;
}

export interface Sentiments {
  positivo: number;
  neutral: number;
  negativo: number;
}

export interface IntentPosition {
  first_intent: number;
  post_consultation: number;
  first_intent_pct: number;
}

export interface GreetingContamination {
  pure_greeting_count: number;
  with_real_intent: number;
  no_greeting: number;
}

export interface Redirections {
  total: number;
  pct: number;
  by_channel: Record<string, number>;
}

export interface Utility {
  useful: number;
  not_useful: number;
  no_survey: number;
  useful_pct: number;
}

export interface BotFailures {
  total: number;
  pct: number;
  by_criteria: Record<string, number>;
}

export interface AdvisorEscalation {
  total: number;
  pct: number;
}

export interface UnderlyingIntent {
  category: string;
  threads: number;
  pct: number;
}

interface Subcategory {
  name: string;
  conversations: number;
  pct_within_macro: number;
  user_phrases: UserPhrase[];
  products: Product[];
  sentiments: Sentiments;
  intent_position: IntentPosition;
  greeting_contamination: GreetingContamination;
  redirections: Redirections;
  utility: Utility;
  bot_failures: BotFailures;
  advisor_escalation?: AdvisorEscalation;
  underlying_intents?: UnderlyingIntent[];
}

interface MacroCategory {
  macro: string;
  total_conversations: number;
  pct: number;
  subcategories: Subcategory[];
}

interface ThreadItem {
  thread_id: string;
  first_human_message: string;
  message_count: number;
  intent_position: string;
  product: string;
  sentiment: string;
  fecha: string;
  was_redirected: boolean;
  redirect_channel: string;
  survey_result: string;
  bot_failed: boolean;
  failure_criteria: string;
}

export function N(n: number): string {
  return Math.round(n).toLocaleString('es-CO');
}

export const CHANNEL_LABELS: Record<string, { label: string; icon: typeof Phone }> = {
  serviline: { label: 'Servilinea', icon: Phone },
  digital: { label: 'Digital', icon: Monitor },
  office: { label: 'Oficina', icon: Building2 },
  other: { label: 'Otro', icon: ArrowRight },
};

export function SentimentBar({ s }: { s: Sentiments }) {
  const total = s.positivo + s.neutral + s.negativo;
  if (!total) return null;
  const pos = (s.positivo / total) * 100;
  const neu = (s.neutral / total) * 100;
  const neg = (s.negativo / total) * 100;
  return (
    <div>
      <div className="flex h-2 rounded-full overflow-hidden gap-px">
        {pos > 0 && <div className="bg-green-400" style={{ width: `${pos}%` }} title={`Positivo ${pos.toFixed(1)}%`} />}
        {neu > 0 && <div className="bg-gray-200" style={{ width: `${neu}%` }} title={`Neutral ${neu.toFixed(1)}%`} />}
        {neg > 0 && <div className="bg-rose-400" style={{ width: `${neg}%` }} title={`Negativo ${neg.toFixed(1)}%`} />}
      </div>
      <div className="flex gap-3 mt-1.5 text-xs">
        <span className="text-green-600 font-medium">{pos.toFixed(0)}% pos.</span>
        <span className="text-gray-400">{neu.toFixed(0)}% neu.</span>
        <span className="text-rose-500 font-medium">{neg.toFixed(0)}% neg.</span>
      </div>
    </div>
  );
}

export function OutcomeCards({ sub }: { sub: Subcategory }) {
  const ip = sub.intent_position;
  const rd = sub.redirections;
  const ut = sub.utility;
  const bf = sub.bot_failures;
  const ae = sub.advisor_escalation;

  return (
    <div className="grid grid-cols-2 md:grid-cols-5 gap-3 px-5 py-3">
      {/* Intent Position */}
      <div className="bg-white border border-blue-100 rounded-lg p-3">
        <div className="text-[10px] font-semibold text-blue-600 uppercase tracking-wider mb-2">Intencion original</div>
        <div className="text-xl font-bold text-blue-700">{ip.first_intent_pct}%</div>
        <div className="flex h-1.5 rounded-full overflow-hidden gap-px mt-2">
          <div className="bg-blue-400" style={{ width: `${ip.first_intent_pct}%` }} />
          <div className="bg-amber-300" style={{ width: `${100 - ip.first_intent_pct}%` }} />
        </div>
        <div className="flex justify-between mt-1.5 text-[10px] text-gray-500">
          <span>{N(ip.first_intent)} 1ra intencion</span>
          <span>{N(ip.post_consultation)} post-consulta</span>
        </div>
        <div className="mt-2 text-[10px] text-blue-500/70">
          {ip.first_intent_pct >= 70
            ? 'La mayoría llega buscando esto directamente'
            : ip.first_intent_pct >= 40
              ? 'Mezcla de intención directa y consulta posterior'
              : 'La mayoría llega aquí después de otra consulta'}
        </div>
      </div>

      {/* Redirections */}
      <div className="bg-white border border-orange-100 rounded-lg p-3">
        <div className="text-[10px] font-semibold text-orange-600 uppercase tracking-wider mb-2">Redirecciones</div>
        <div className="text-xl font-bold text-orange-700">{rd.pct}%</div>
        <div className="text-[10px] text-gray-500 mt-1">{N(rd.total)} de {N(sub.conversations)} redirigidas</div>
        {rd.total > 0 && (
          <div className="mt-2 space-y-1">
            {(['serviline', 'digital', 'office'] as const).map(ch => {
              const count = rd.by_channel[ch] || 0;
              if (count === 0) return null;
              const info = CHANNEL_LABELS[ch];
              const Icon = info.icon;
              const chPct = rd.total > 0 ? Math.round(count / rd.total * 100) : 0;
              return (
                <div key={ch} className="flex items-center gap-1.5 text-[10px] text-gray-600">
                  <Icon size={10} className="text-orange-400" />
                  <span>{info.label}</span>
                  <span className="ml-auto font-medium">{N(count)}</span>
                  <span className="text-gray-400">({chPct}%)</span>
                </div>
              );
            })}
            {(rd.by_channel['other'] || 0) > 0 && (
              <div className="flex items-center gap-1.5 text-[10px] text-gray-600">
                <ArrowRight size={10} className="text-orange-400" />
                <span>Otro</span>
                <span className="ml-auto font-medium">{N(rd.by_channel['other'])}</span>
                <span className="text-gray-400">({Math.round((rd.by_channel['other'] || 0) / rd.total * 100)}%)</span>
              </div>
            )}
          </div>
        )}
      </div>

      {/* Utility */}
      <div className="bg-white border border-green-100 rounded-lg p-3">
        <div className="text-[10px] font-semibold text-green-600 uppercase tracking-wider mb-2">Utilidad (encuesta)</div>
        <div className="text-xl font-bold text-green-700">
          {(ut.useful + ut.not_useful) > 0 ? `${ut.useful_pct}%` : 'N/A'}
        </div>
        <div className="flex h-1.5 rounded-full overflow-hidden gap-px mt-2">
          {ut.useful > 0 && <div className="bg-green-400" style={{ width: `${ut.useful_pct}%` }} />}
          {ut.not_useful > 0 && <div className="bg-rose-400" style={{ width: `${100 - ut.useful_pct}%` }} />}
        </div>
        <div className="mt-1.5 space-y-0.5 text-[10px] text-gray-500">
          <div className="flex justify-between"><span className="text-green-600">{N(ut.useful)} util</span><span className="text-rose-500">{N(ut.not_useful)} no util</span></div>
          <div className="text-gray-400">{N(ut.no_survey)} sin encuesta</div>
        </div>
      </div>

      {/* Bot Failures */}
      <div className="bg-white border border-rose-100 rounded-lg p-3">
        <div className="text-[10px] font-semibold text-rose-600 uppercase tracking-wider mb-2">Fallos del bot</div>
        <div className="text-xl font-bold text-rose-700">{bf.pct}%</div>
        <div className="text-[10px] text-gray-500 mt-1">{N(bf.total)} de {N(sub.conversations)} fallaron</div>
        {Object.entries(bf.by_criteria).length > 0 && (
          <div className="mt-2 space-y-1">
            {Object.entries(bf.by_criteria).map(([crit, count]) => (
              <div key={crit} className="flex items-center gap-1.5 text-[10px] text-gray-600">
                <AlertTriangle size={9} className="text-rose-400 shrink-0" />
                <span className="truncate">{crit}</span>
                <span className="ml-auto font-medium shrink-0">{N(count as number)}</span>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Advisor Escalation */}
      {ae && ae.total > 0 && (
        <div className="bg-white border border-violet-100 rounded-lg p-3">
          <div className="text-[10px] font-semibold text-violet-600 uppercase tracking-wider mb-2">Escalacion a asesor</div>
          <div className="text-xl font-bold text-violet-700">{ae.pct}%</div>
          <div className="text-[10px] text-gray-500 mt-1">{N(ae.total)} pidieron asesor despues</div>
          <div className="mt-2 text-[10px] text-violet-500">
            El usuario consulto primero y luego solicito hablar con un asesor
          </div>
        </div>
      )}
    </div>
  );
}

export function ThreadListPanel({
  macro,
  subcategory,
  product,
  crossCategory,
  onNavigateToThread,
  startDate,
  endDate,
}: {
  macro: string;
  subcategory?: string;
  product?: string;
  crossCategory?: string;
  onNavigateToThread?: (threadId: string) => void;
  startDate?: string;
  endDate?: string;
}) {
  const [threads, setThreads] = useState<ThreadItem[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(false);
  const limit = 15;

  const load = useCallback(() => {
    setLoading(true);
    api.getCategoryThreads({
      macro,
      subcategory,
      product,
      cross_category: crossCategory,
      page,
      limit,
      start_date: startDate,
      end_date: endDate,
    })
      .then(r => { setThreads(r.data); setTotal(r.total); })
      .catch(console.error)
      .finally(() => setLoading(false));
  }, [macro, subcategory, product, crossCategory, page, startDate, endDate]);

  useEffect(() => { load(); }, [load]);

  const totalPages = Math.ceil(total / limit);

  return (
    <div className="px-5 py-3 bg-gray-50/80 border-t border-gray-100">
      <div className="flex items-center justify-between mb-3">
        <div className="text-xs font-semibold text-gray-500 uppercase tracking-wider">
          Conversaciones {product ? `(${product})` : ''}{crossCategory ? ` + ${crossCategory}` : ''} - {N(total)} hilos
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

      {loading ? (
        <div className="text-xs text-gray-400 text-center py-4">Cargando...</div>
      ) : threads.length === 0 ? (
        <div className="text-xs text-gray-400 text-center py-4">Sin conversaciones</div>
      ) : (
        <div className="overflow-x-auto">
          <table className="w-full text-xs">
            <thead>
              <tr className="text-left text-gray-500 border-b border-gray-200">
                <th className="py-2 pr-2 font-medium">Fecha</th>
                <th className="py-2 pr-2 font-medium">Thread</th>
                <th className="py-2 pr-2 font-medium">Primer mensaje</th>
                <th className="py-2 pr-2 font-medium">Producto</th>
                <th className="py-2 pr-2 font-medium text-center">Intencion</th>
                <th className="py-2 pr-2 font-medium text-center">Redirigida</th>
                <th className="py-2 pr-2 font-medium text-center">Encuesta</th>
                <th className="py-2 pr-2 font-medium text-center">Fallo</th>
              </tr>
            </thead>
            <tbody>
              {threads.map(t => (
                <tr key={t.thread_id} className="border-b border-gray-50 hover:bg-white/60">
                  <td className="py-2 pr-2 text-gray-500 whitespace-nowrap">{t.fecha}</td>
                  <td className="py-2 pr-2">
                    <button
                      onClick={() => onNavigateToThread?.(t.thread_id)}
                      className="text-violet-600 hover:text-violet-800 hover:underline font-mono text-[10px] flex items-center gap-1"
                      title="Ver hilo completo"
                    >
                      {t.thread_id.slice(0, 12)}...
                      <ExternalLink size={10} />
                    </button>
                    <span className="text-[10px] text-gray-400">{t.message_count} msgs</span>
                  </td>
                  <td className="py-2 pr-2 text-gray-700 max-w-xs truncate">{t.first_human_message}</td>
                  <td className="py-2 pr-2 text-gray-500">{t.product || '-'}</td>
                  <td className="py-2 pr-2 text-center">
                    <Badge variant={t.intent_position === 'first_intent' ? 'primary' : 'warning'} className="text-[10px]">
                      {t.intent_position === 'first_intent' ? '1ra' : 'Post'}
                    </Badge>
                  </td>
                  <td className="py-2 pr-2 text-center">
                    {t.was_redirected ? (
                      <Badge variant="orange" className="text-[10px]">
                        {CHANNEL_LABELS[t.redirect_channel]?.label || 'Si'}
                      </Badge>
                    ) : (
                      <span className="text-gray-300">-</span>
                    )}
                  </td>
                  <td className="py-2 pr-2 text-center">
                    {t.survey_result === 'useful' && <ThumbsUp size={13} className="inline text-green-500" />}
                    {t.survey_result === 'not_useful' && <ThumbsDown size={13} className="inline text-rose-500" />}
                    {!t.survey_result && <span className="text-gray-300">-</span>}
                  </td>
                  <td className="py-2 pr-2 text-center">
                    {t.bot_failed ? (
                      <span title={t.failure_criteria}><AlertTriangle size={13} className="inline text-rose-500" /></span>
                    ) : (
                      <span className="text-gray-300">-</span>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}


function SubcategoryDetail({
  sub,
  macro,
  onNavigateToThread,
  startDate,
  endDate,
}: {
  sub: Subcategory;
  macro: string;
  onNavigateToThread?: (threadId: string) => void;
  startDate?: string;
  endDate?: string;
}) {
  const [showThreads, setShowThreads] = useState(false);
  const [threadProduct, setThreadProduct] = useState<string | undefined>();
  const [threadCrossCategory, setThreadCrossCategory] = useState<string | undefined>();

  return (
    <div>
      {/* Row 1: Outcome metrics */}
      <OutcomeCards sub={sub} />

      {/* Row 2: Detail columns */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-5 px-5 py-4 bg-gray-50/60">
        {/* User phrases */}
        <div>
          <div className="flex items-center gap-1.5 text-xs font-semibold text-gray-500 uppercase tracking-wider mb-3">
            <MessageSquare size={11} />
            Preguntas frecuentes
          </div>
          {sub.user_phrases.length === 0 ? (
            <p className="text-xs text-gray-400 italic">Sin datos</p>
          ) : (
            <ul className="space-y-2">
              {sub.user_phrases.map((p, i) => (
                <li key={i} className="flex items-start gap-2 text-xs">
                  <Badge variant="violet" className="shrink-0 text-[10px] px-1.5 py-0.5 rounded">
                    {p.count}x
                  </Badge>
                  <span className="text-gray-700 line-clamp-2">{p.phrase}</span>
                </li>
              ))}
            </ul>
          )}
        </div>

        {/* Products — clickable */}
        <div>
          <div className="flex items-center gap-1.5 text-xs font-semibold text-gray-500 uppercase tracking-wider mb-3">
            <Package size={11} />
            Productos asociados
          </div>
          {sub.products.length === 0 ? (
            <p className="text-xs text-gray-400 italic">Sin datos</p>
          ) : (
            <table className="w-full text-xs">
              <tbody>
                {sub.products.map((p, i) => (
                  <tr
                    key={i}
                    className={cn(
                      'border-b border-gray-100 last:border-0 cursor-pointer hover:bg-violet-50 transition-colors',
                      i % 2 === 0 ? '' : 'bg-white/60',
                    )}
                    onClick={() => {
                      setThreadProduct(p.name);
                      setShowThreads(true);
                    }}
                    title={`Ver conversaciones de ${p.name}`}
                  >
                    <td className="py-1.5 text-gray-600">{p.name || '-'}</td>
                    <td className="py-1.5 text-right font-semibold text-gray-800">{N(p.conversations)}</td>
                    <td className="py-1.5 pl-2 text-right"><ExternalLink size={10} className="text-gray-300" /></td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>

        {/* Sentiment */}
        <div>
          <div className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-3">
            Sentimiento
          </div>
          <SentimentBar s={sub.sentiments} />
          <div className="mt-3 space-y-1 text-xs">
            {[
              { label: 'Positivo', count: sub.sentiments.positivo, cls: 'text-green-600' },
              { label: 'Neutral', count: sub.sentiments.neutral, cls: 'text-gray-500' },
              { label: 'Negativo', count: sub.sentiments.negativo, cls: 'text-rose-500' },
            ].map(({ label, count, cls }) => (
              <div key={label} className="flex justify-between items-center">
                <span className={cn('font-medium', cls)}>{label}</span>
                <span className="text-gray-700 tabular-nums">{N(count)}</span>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Row 3: Underlying intents — clickable like products */}
      {sub.underlying_intents && sub.underlying_intents.length > 0 && (
        <div className="px-5 py-3 border-t border-gray-100 bg-amber-50/40">
          <div className="flex items-center gap-1.5 text-xs font-semibold text-amber-700 uppercase tracking-wider mb-2">
            <Search size={11} />
            Intenciones subyacentes
          </div>
          <p className="text-[10px] text-amber-600/70 mb-2">
            Otras solicitudes que aparecen en las mismas conversaciones — click para ver los hilos
          </p>
          <table className="w-full text-xs max-w-lg">
            <tbody>
              {sub.underlying_intents.map((ui, i) => (
                <tr
                  key={i}
                  className={cn(
                    'border-b border-amber-100 last:border-0 cursor-pointer hover:bg-amber-100/60 transition-colors',
                    i % 2 === 0 ? '' : 'bg-white/40',
                  )}
                  onClick={() => {
                    setThreadProduct(undefined);
                    setThreadCrossCategory(ui.category);
                    setShowThreads(true);
                  }}
                  title={`Ver conversaciones de ${sub.name} + ${ui.category}`}
                >
                  <td className="py-1.5 text-gray-700">{ui.category}</td>
                  <td className="py-1.5 text-right font-semibold text-amber-800 tabular-nums">{N(ui.threads)}</td>
                  <td className="py-1.5 pl-1 text-right text-gray-400 tabular-nums">{ui.pct}%</td>
                  <td className="py-1.5 pl-2 text-right"><ExternalLink size={10} className="text-amber-300" /></td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Toggle thread list */}
      <div className="px-5 py-2 border-t border-gray-100 bg-gray-50/40">
        <button
          onClick={() => { setThreadProduct(undefined); setThreadCrossCategory(undefined); setShowThreads(!showThreads); }}
          className="text-xs text-violet-600 hover:text-violet-800 font-medium hover:underline"
        >
          {showThreads && !threadProduct && !threadCrossCategory ? 'Ocultar conversaciones' : `Ver ${N(sub.conversations)} conversaciones`}
        </button>
        {showThreads && threadProduct && (
          <button
            onClick={() => { setThreadProduct(undefined); }}
            className="ml-3 text-xs text-gray-500 hover:text-gray-700"
          >
            Quitar filtro de producto
          </button>
        )}
        {showThreads && threadCrossCategory && (
          <button
            onClick={() => { setThreadCrossCategory(undefined); }}
            className="ml-3 text-xs text-amber-600 hover:text-amber-800"
          >
            Quitar filtro: {threadCrossCategory}
          </button>
        )}
      </div>

      {/* Thread list */}
      {showThreads && (
        <ThreadListPanel
          macro={macro}
          subcategory={sub.name}
          product={threadProduct}
          crossCategory={threadCrossCategory}
          onNavigateToThread={onNavigateToThread}
          startDate={startDate}
          endDate={endDate}
        />
      )}
    </div>
  );
}

export function CategoriesDeepPanel({
  onNavigateToThread,
  startDate,
  endDate,
}: {
  onNavigateToThread?: (threadId: string) => void;
  startDate?: string;
  endDate?: string;
}) {
  const [data, setData] = useState<MacroCategory[]>([]);
  const [loading, setLoading] = useState(true);
  const [openMacro, setOpenMacro] = useState<string>('');
  const [openSub, setOpenSub] = useState<string>('');
  const [search, setSearch] = useState('');

  useEffect(() => {
    api.getCategoriesDetailed({ start_date: startDate, end_date: endDate })
      .then((d: MacroCategory[]) => {
        setData(d);
        if (d.length > 0) setOpenMacro(d[0].macro);
      })
      .catch(console.error)
      .finally(() => setLoading(false));
  }, [startDate, endDate]);

  const filtered = search.trim()
    ? data.filter(m =>
        m.macro.toLowerCase().includes(search.toLowerCase()) ||
        m.subcategories.some(s => s.name.toLowerCase().includes(search.toLowerCase()))
      )
    : data;

  if (loading) {
    return <div className="flex items-center justify-center h-64 text-gray-400 text-sm">Cargando categorias...</div>;
  }

  return (
    <div className="space-y-4">
      {/* Search */}
      <div className="flex items-center gap-3">
        <div className="relative flex-1">
          <Search size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
          <input
            type="text"
            value={search}
            onChange={e => setSearch(e.target.value)}
            placeholder="Buscar macro o subcategoria..."
            className="w-full border border-gray-200 rounded-lg pl-9 pr-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-violet-300 bg-white"
          />
        </div>
        <Badge variant="default" className="shrink-0">{filtered.length} macros</Badge>
      </div>

      {/* Macro accordion */}
      <Accordion
        type="single"
        collapsible
        value={openMacro}
        onValueChange={v => { setOpenMacro(v); setOpenSub(''); }}
        className="space-y-3"
      >
        {filtered.map(macro => (
          <AccordionItem
            key={macro.macro}
            value={macro.macro}
            className="bg-white rounded-xl border border-gray-200 shadow-sm overflow-hidden"
          >
            <AccordionTrigger className="px-5 py-4 hover:bg-gray-50 rounded-none">
              <div className="flex items-center gap-3 flex-wrap">
                <Layers size={16} className="text-violet-600 shrink-0" />
                <span className="font-semibold text-gray-800">{macro.macro}</span>
                <Badge variant="violet">{N(macro.total_conversations)} conv.</Badge>
                <span className="text-xs text-gray-400">{macro.pct.toFixed(1)}% del total</span>
              </div>
            </AccordionTrigger>

            <AccordionContent className="p-0 pb-0">
              <Separator />
              {/* Sub-accordion */}
              <Accordion
                type="single"
                collapsible
                value={openSub}
                onValueChange={setOpenSub}
              >
                {macro.subcategories.map(sub => {
                  const subKey = `${macro.macro}::${sub.name}`;
                  const greetPct = sub.conversations > 0
                    ? (sub.greeting_contamination?.pure_greeting_count || 0) / sub.conversations * 100
                    : 0;
                  return (
                    <AccordionItem
                      key={subKey}
                      value={subKey}
                      className="border-b border-gray-50 last:border-0"
                    >
                      <AccordionTrigger className="px-7 py-3 hover:bg-gray-50 text-left">
                        <div className="flex items-center gap-3 flex-wrap">
                          <div className="w-2 h-2 rounded-full bg-violet-300 shrink-0" />
                          <span className="text-sm text-gray-700 font-medium">{sub.name}</span>
                          <span className="text-xs text-gray-500 tabular-nums">{N(sub.conversations)} conv.</span>
                          <span className="text-xs text-gray-300">({sub.pct_within_macro.toFixed(1)}% del macro)</span>
                          {sub.redirections && sub.redirections.pct > 20 && (
                            <Badge variant="orange" className="text-[10px]">{sub.redirections.pct}% redir.</Badge>
                          )}
                          {sub.bot_failures && sub.bot_failures.pct > 30 && (
                            <Badge variant="danger" className="text-[10px]">{sub.bot_failures.pct}% fallos</Badge>
                          )}
                          {sub.advisor_escalation && sub.advisor_escalation.pct > 10 && (
                            <Badge variant="violet" className="text-[10px]">{sub.advisor_escalation.pct}% piden asesor</Badge>
                          )}
                          {greetPct > 5 && (
                            <Badge variant="warning" className="text-[10px]">{greetPct.toFixed(0)}% saludos</Badge>
                          )}
                        </div>
                      </AccordionTrigger>
                      <AccordionContent className="p-0 pb-0">
                        <SubcategoryDetail
                          sub={sub}
                          macro={macro.macro}
                          onNavigateToThread={onNavigateToThread}
                          startDate={startDate}
                          endDate={endDate}
                        />
                      </AccordionContent>
                    </AccordionItem>
                  );
                })}
              </Accordion>
            </AccordionContent>
          </AccordionItem>
        ))}
      </Accordion>
    </div>
  );
}
