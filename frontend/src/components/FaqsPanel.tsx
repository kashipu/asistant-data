import { useEffect, useState } from 'react';
import { api } from '../services/api';
import { Loader2, Bookmark, MessageSquare, Copy, Check, Download, ChevronDown, ChevronRight } from 'lucide-react';
import * as XLSX from 'xlsx';

interface FaqItem {
  phrase: string;
  count: number;
}

// New shape: { macro: { subcategory: FaqItem[] } }
type FaqData = Record<string, Record<string, FaqItem[]>>;

const MACRO_COLORS: Record<string, string> = {
  'Transferencias':      'bg-blue-600',
  'Pagos':               'bg-green-600',
  'Tarjetas':            'bg-purple-600',
  'Créditos y Préstamos':'bg-orange-600',
  'Cuentas y Productos': 'bg-teal-600',
  'Seguridad y Accesos': 'bg-red-600',
  'App y Canales':       'bg-yellow-600',
  'Gestión Personal':    'bg-pink-600',
  'Información':         'bg-indigo-600',
  'Experiencia':         'bg-gray-600',
};

export function FaqsPanel() {
  const [data, setData] = useState<FaqData>({});
  const [loading, setLoading] = useState(true);
  const [copied, setCopied] = useState<string | null>(null);
  const [collapsedMacros, setCollapsedMacros] = useState<Record<string, boolean>>({});

  useEffect(() => {
    const fetchData = async () => {
      setLoading(true);
      try {
        const result = await api.getFaqs(25);
        setData(result);
      } catch (err) {
        console.error(err);
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, []);

  const handleCopy = (text: string) => {
    navigator.clipboard.writeText(text);
    setCopied(text);
    setTimeout(() => setCopied(null), 2000);
  };

  const toggleMacro = (macro: string) => {
    setCollapsedMacros(prev => ({ ...prev, [macro]: !prev[macro] }));
  };

  const exportToExcel = () => {
    const rows: { "Macro": string; "Subcategoría": string; "Caso de Prueba (Frase)": string; "Frecuencia (Veces)": number }[] = [];
    Object.keys(data).sort().forEach(macro => {
      Object.keys(data[macro]).sort().forEach(sub => {
        data[macro][sub].forEach(item => {
          rows.push({
            "Macro": macro,
            "Subcategoría": sub,
            "Caso de Prueba (Frase)": item.phrase,
            "Frecuencia (Veces)": item.count,
          });
        });
      });
    });

    const worksheet = XLSX.utils.json_to_sheet(rows);
    const workbook = XLSX.utils.book_new();
    XLSX.utils.book_append_sheet(workbook, worksheet, "Casos de Prueba");
    const maxPhrase = rows.length ? Math.max(...rows.map(r => r["Caso de Prueba (Frase)"].length), 30) : 30;
    worksheet['!cols'] = [{ wch: 22 }, { wch: 28 }, { wch: Math.min(maxPhrase, 80) }, { wch: 18 }];
    XLSX.writeFile(workbook, "Casos_De_Prueba_Asistente.xlsx");
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center p-12">
        <Loader2 className="w-8 h-8 animate-spin text-blue-500" />
      </div>
    );
  }

  const sortedMacros = Object.keys(data).sort();

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-gradient-to-r from-blue-50 to-white p-6 rounded-xl border border-gray-100 shadow-sm flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-xl font-bold flex items-center gap-2 text-gray-800">
            <Bookmark className="text-blue-500" />
            Módulo de Casos de Prueba (FAQs)
          </h2>
          <p className="text-gray-600 mt-2 text-sm">
            Frases <b>exactas</b> más frecuentes de usuarios reales, agrupadas por categoría y subcategoría.
            Úsalas como <b>Casos de Prueba</b> para auditar el flujo conversacional del asistente.
          </p>
        </div>
        <button
          onClick={exportToExcel}
          className="shrink-0 flex items-center gap-2 bg-green-600 hover:bg-green-700 text-white px-4 py-2 rounded-lg text-sm font-medium shadow-sm transition-colors"
        >
          <Download className="w-4 h-4" />
          Exportar a Excel
        </button>
      </div>

      {/* Macro groups */}
      <div className="space-y-4">
        {sortedMacros.map(macro => {
          const color = MACRO_COLORS[macro] ?? 'bg-gray-600';
          const isCollapsed = collapsedMacros[macro] ?? false;
          const subcats = Object.keys(data[macro]).sort();
          const totalPhrases = subcats.reduce((acc, s) => acc + data[macro][s].length, 0);

          return (
            <div key={macro} className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
              {/* Macro header — clickable to collapse */}
              <button
                onClick={() => toggleMacro(macro)}
                className="w-full flex items-center justify-between px-5 py-4 hover:bg-gray-50 transition-colors"
              >
                <div className="flex items-center gap-3">
                  <span className={`${color} text-white text-xs font-bold px-2.5 py-1 rounded-full`}>
                    {macro}
                  </span>
                  <span className="text-sm text-gray-500">
                    {subcats.length} subcategoría{subcats.length !== 1 ? 's' : ''} · {totalPhrases} frases
                  </span>
                </div>
                {isCollapsed
                  ? <ChevronRight className="w-4 h-4 text-gray-400" />
                  : <ChevronDown className="w-4 h-4 text-gray-400" />
                }
              </button>

              {/* Subcategories grid */}
              {!isCollapsed && (
                <div className="border-t border-gray-100 grid grid-cols-1 lg:grid-cols-2 divide-y lg:divide-y-0 lg:divide-x divide-gray-100">
                  {subcats.map(sub => {
                    const phrases = data[macro][sub];
                    const visible = phrases.slice(0, 10);
                    const extra = phrases.length - 10;
                    return (
                      <div key={sub} className="flex flex-col">
                        <div className="bg-gray-50 px-4 py-2.5 text-sm font-semibold text-gray-700 border-b border-gray-100">
                          {sub}
                        </div>
                        <ul className="divide-y divide-gray-50 flex-1">
                          {visible.map((item, idx) => (
                            <li key={idx} className="flex items-start gap-3 px-4 py-3 hover:bg-gray-50 transition-colors group">
                              <MessageSquare className="w-4 h-4 text-gray-300 shrink-0 mt-0.5" />
                              <div className="flex-1 min-w-0">
                                <p className="text-sm text-gray-800 break-words">"{item.phrase}"</p>
                                <p className="text-xs text-gray-400 mt-0.5">Repetido {item.count} veces</p>
                              </div>
                              <button
                                onClick={() => handleCopy(item.phrase)}
                                className="p-1.5 bg-white border shadow-sm rounded-md text-gray-400 hover:text-blue-600 hover:bg-blue-50 transition-colors opacity-0 group-hover:opacity-100"
                                title="Copiar texto"
                              >
                                {copied === item.phrase ? <Check className="w-3.5 h-3.5 text-green-500" /> : <Copy className="w-3.5 h-3.5" />}
                              </button>
                            </li>
                          ))}
                        </ul>
                        {extra > 0 && (
                          <div className="bg-gray-50 px-4 py-2 border-t border-gray-100 text-xs text-gray-400 text-center">
                            + {extra} casos adicionales en la exportación Excel
                          </div>
                        )}
                      </div>
                    );
                  })}
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
