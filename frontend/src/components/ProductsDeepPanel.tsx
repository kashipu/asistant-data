import { useEffect, useState } from 'react';
import { api } from '../services/api';
import { Package, Layers, MessageSquare, Search, AlertTriangle, ExternalLink } from 'lucide-react';
import { Badge } from '@/components/ui/badge';
import { Separator } from '@/components/ui/separator';
import {
  Accordion,
  AccordionItem,
  AccordionTrigger,
  AccordionContent,
} from '@/components/ui/accordion';

import {
  N,
  SentimentBar,
  OutcomeCards,
  ThreadListPanel,
  type UserPhrase,
  type Sentiments,
  type IntentPosition,
  type GreetingContamination,
  type Redirections,
  type Utility,
  type BotFailures,
  type AdvisorEscalation,
  type UnderlyingIntent,
} from './CategoriesDeepPanel';

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

interface CategoryItem {
  name: string;
  conversations: number;
  pct: number;
}

interface ProductItem {
  name: string;
  conversations: number;
  pct_within_macro: number;
  top_categories: CategoryItem[];
  sentiments: Sentiments;
  user_phrases: UserPhrase[];
  intent_position: IntentPosition;
  greeting_contamination: GreetingContamination;
  redirections: Redirections;
  utility: Utility;
  bot_failures: BotFailures;
  advisor_escalation?: AdvisorEscalation;
  underlying_intents?: UnderlyingIntent[];
}

interface ProductMacro {
  macro: string;
  total_conversations: number;
  pct: number;
  products: ProductItem[];
}

interface Props {
  onNavigateToThread?: (threadId: string) => void;
  startDate?: string;
  endDate?: string;
}

// ---------------------------------------------------------------------------
// ProductDetail — expanded content for a single product
// ---------------------------------------------------------------------------

function ProductDetail({
  prod,
  macroName,
  onNavigateToThread,
  startDate,
  endDate,
}: {
  prod: ProductItem;
  macroName: string;
  onNavigateToThread?: (threadId: string) => void;
  startDate?: string;
  endDate?: string;
}) {
  const [showThreads, setShowThreads] = useState(false);
  const [threadCategory, setThreadCategory] = useState<string | undefined>();

  // OutcomeCards expects a "sub" shaped object — ProductItem already has the same fields
  const subShaped = {
    ...prod,
    name: prod.name,
    products: [] as { name: string; conversations: number }[],
  };

  return (
    <div className="space-y-4">
      {/* Outcome Cards */}
      <OutcomeCards sub={subShaped} />

      <Separator />

      {/* Three-column detail grid */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-5 px-5 py-3">
        {/* Categories associated */}
        <div>
          <div className="flex items-center gap-1.5 text-xs font-semibold text-gray-500 uppercase tracking-wider mb-3">
            <Layers size={11} /> Categorias asociadas
          </div>
          {prod.top_categories.length > 0 ? (
            <div className="space-y-1">
              {prod.top_categories.map((cat, i) => (
                <button
                  key={i}
                  onClick={() => {
                    setThreadCategory(cat.name);
                    setShowThreads(true);
                  }}
                  className="flex items-center justify-between w-full text-xs hover:bg-gray-50 rounded-lg px-2 py-1.5 transition-colors text-left"
                >
                  <span className="text-gray-700 truncate pr-2">{cat.name}</span>
                  <div className="flex items-center gap-2 shrink-0">
                    <span className="font-semibold text-gray-800 tabular-nums">{N(cat.conversations)}</span>
                    <span className="text-gray-400 text-[10px]">{cat.pct}%</span>
                    <ExternalLink size={10} className="text-gray-300" />
                  </div>
                </button>
              ))}
            </div>
          ) : (
            <div className="text-xs text-gray-400 italic">Sin datos</div>
          )}
        </div>

        {/* User phrases */}
        <div>
          <div className="flex items-center gap-1.5 text-xs font-semibold text-gray-500 uppercase tracking-wider mb-3">
            <MessageSquare size={11} /> Que pregunta el usuario
          </div>
          {prod.user_phrases.length > 0 ? (
            <div className="space-y-2">
              {prod.user_phrases.map((p, i) => (
                <div key={i} className="flex items-start gap-2 text-xs">
                  <span className="text-gray-700 leading-relaxed flex-1">{p.phrase}</span>
                  <Badge variant="violet" className="text-[10px] shrink-0">{p.count}</Badge>
                </div>
              ))}
            </div>
          ) : (
            <div className="text-xs text-gray-400 italic">Sin datos</div>
          )}
        </div>

        {/* Sentiment */}
        <div>
          <div className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-3">Sentimiento</div>
          <SentimentBar s={prod.sentiments} />
          <div className="mt-3 space-y-1 text-xs text-gray-500">
            <div className="flex justify-between"><span>Positivo</span><span className="font-medium">{N(prod.sentiments.positivo)}</span></div>
            <div className="flex justify-between"><span>Neutral</span><span className="font-medium">{N(prod.sentiments.neutral)}</span></div>
            <div className="flex justify-between"><span>Negativo</span><span className="font-medium">{N(prod.sentiments.negativo)}</span></div>
          </div>
        </div>
      </div>

      {/* Underlying intents */}
      {prod.underlying_intents && prod.underlying_intents.length > 0 && (
        <div className="mx-5 p-4 bg-amber-50/40 rounded-xl border border-amber-100">
          <div className="flex items-center gap-1.5 text-xs font-semibold text-amber-700 uppercase tracking-wider mb-3">
            <Search size={11} /> Intenciones subyacentes
          </div>
          <div className="space-y-1">
            {prod.underlying_intents.map((ui, i) => (
              <button
                key={i}
                onClick={() => {
                  setThreadCategory(ui.category);
                  setShowThreads(true);
                }}
                className="flex items-center justify-between w-full text-xs hover:bg-amber-100/50 rounded-lg px-2 py-1.5 transition-colors text-left"
              >
                <span className="text-amber-800 truncate pr-2">{ui.category}</span>
                <div className="flex items-center gap-2 shrink-0">
                  <span className="font-semibold text-amber-900 tabular-nums">{N(ui.threads)}</span>
                  <span className="text-amber-600 text-[10px]">{ui.pct}%</span>
                </div>
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Thread list toggle */}
      <div className="px-5 pb-3 space-y-2">
        <div className="flex items-center gap-2">
          <button
            onClick={() => { setShowThreads(!showThreads); setThreadCategory(undefined); }}
            className="text-xs font-medium text-violet-600 hover:text-violet-800 hover:underline"
          >
            {showThreads ? 'Ocultar conversaciones' : 'Ver conversaciones'}
          </button>
          {threadCategory && (
            <button
              onClick={() => setThreadCategory(undefined)}
              className="text-[10px] bg-amber-100 text-amber-700 px-2 py-0.5 rounded-full hover:bg-amber-200"
            >
              Quitar filtro: {threadCategory}
            </button>
          )}
        </div>
        {showThreads && (
          <ThreadListPanel
            macro={macroName}
            product={prod.name}
            subcategory={threadCategory}
            onNavigateToThread={onNavigateToThread}
            startDate={startDate}
            endDate={endDate}
          />
        )}
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// ProductsDeepPanel — Main component
// ---------------------------------------------------------------------------

export function ProductsDeepPanel({ onNavigateToThread, startDate, endDate }: Props) {
  const [data, setData] = useState<ProductMacro[]>([]);
  const [loading, setLoading] = useState(true);
  const [openMacro, setOpenMacro] = useState('');
  const [openProd, setOpenProd] = useState('');
  const [search, setSearch] = useState('');

  useEffect(() => {
    api.getProductsDetailed({ start_date: startDate, end_date: endDate })
      .then((d: ProductMacro[]) => {
        setData(d);
        if (d.length > 0) setOpenMacro(d[0].macro);
      })
      .catch(console.error)
      .finally(() => setLoading(false));
  }, [startDate, endDate]);

  if (loading) {
    return <div className="flex items-center justify-center h-64 text-gray-400 text-sm">Cargando productos...</div>;
  }

  if (!data.length) {
    return <div className="text-center py-12 text-gray-400 text-sm">No se encontraron datos de productos.</div>;
  }

  const searchLower = search.toLowerCase();
  const filteredData = search.trim()
    ? data
        .map(m => ({
          ...m,
          products: m.products.filter(
            p => p.name.toLowerCase().includes(searchLower) || m.macro.toLowerCase().includes(searchLower)
          ),
        }))
        .filter(m => m.products.length > 0)
    : data;

  return (
    <div className="space-y-5">
      {/* Search */}
      <div className="relative">
        <Search size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
        <input
          type="text"
          value={search}
          onChange={e => setSearch(e.target.value)}
          placeholder="Buscar producto..."
          className="w-full border border-gray-200 rounded-lg pl-9 pr-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-teal-300 bg-white"
        />
      </div>

      {/* Macro Accordion */}
      <Accordion
        type="single"
        collapsible
        value={openMacro}
        onValueChange={setOpenMacro}
        className="space-y-3"
      >
        {filteredData.map(macro => (
          <AccordionItem
            key={macro.macro}
            value={macro.macro}
            className="bg-white rounded-xl border border-gray-200 shadow-sm overflow-hidden"
          >
            <AccordionTrigger className="px-5 py-4 hover:bg-gray-50 rounded-none">
              <div className="flex items-center gap-2 flex-wrap">
                <Package size={16} className="text-teal-600 shrink-0" />
                <span className="font-semibold text-gray-800">{macro.macro}</span>
                <Badge variant="teal">{N(macro.total_conversations)} conv.</Badge>
                <span className="text-xs text-gray-400">{macro.pct}%</span>
              </div>
            </AccordionTrigger>

            <AccordionContent className="p-0 pb-0">
              <Separator />
              <Accordion
                type="single"
                collapsible
                value={openProd}
                onValueChange={setOpenProd}
                className="divide-y divide-gray-100"
              >
                {macro.products.map(prod => (
                  <AccordionItem key={prod.name} value={prod.name}>
                    <AccordionTrigger className="px-5 py-3 hover:bg-gray-50 rounded-none text-sm">
                      <div className="flex items-center gap-2 flex-wrap">
                        <span className="text-gray-700 font-medium">{prod.name}</span>
                        <Badge variant="default">{N(prod.conversations)}</Badge>
                        <span className="text-xs text-gray-400">{prod.pct_within_macro}%</span>
                        {prod.bot_failures.pct > 5 && (
                          <Badge variant="danger" className="text-[10px]">
                            <AlertTriangle size={9} className="mr-0.5" />
                            {prod.bot_failures.pct}% fallos
                          </Badge>
                        )}
                        {prod.redirections.pct > 10 && (
                          <Badge variant="orange" className="text-[10px]">
                            {prod.redirections.pct}% redir.
                          </Badge>
                        )}
                      </div>
                    </AccordionTrigger>
                    <AccordionContent className="p-0 pb-0">
                      <Separator />
                      <ProductDetail
                        prod={prod}
                        macroName={macro.macro}
                        onNavigateToThread={onNavigateToThread}
                        startDate={startDate}
                        endDate={endDate}
                      />
                    </AccordionContent>
                  </AccordionItem>
                ))}
              </Accordion>
            </AccordionContent>
          </AccordionItem>
        ))}
      </Accordion>

      {filteredData.length === 0 && (
        <div className="text-center py-12 text-gray-400 text-sm">
          No se encontraron productos con ese filtro.
        </div>
      )}
    </div>
  );
}
