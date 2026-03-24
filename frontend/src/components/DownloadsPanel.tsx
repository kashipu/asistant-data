import { useEffect, useState } from 'react';
import { api } from '../services/api';
import { FileText, Table, Loader2 } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';

interface Props {
  startDate?: string;
  endDate?: string;
}

interface OptionItem {
  label: string;
  value: string;
}

export function DownloadsPanel({ startDate, endDate }: Props) {
  const [dimension, setDimension] = useState<'product' | 'category'>('product');
  const [selectedValue, setSelectedValue] = useState('');
  const [options, setOptions] = useState<OptionItem[]>([]);
  const [loading, setLoading] = useState(false);
  const [downloading, setDownloading] = useState<'md' | 'csv' | null>(null);

  useEffect(() => {
    setSelectedValue('');
    setLoading(true);

    const fetchOptions = async () => {
      try {
        if (dimension === 'product') {
          const data = await api.getProductsDetailed({
            start_date: startDate || undefined,
            end_date: endDate || undefined,
          });
          const items: OptionItem[] = [];
          for (const macro of data) {
            for (const prod of macro.products || []) {
              items.push({ label: `${prod.name} (${macro.macro})`, value: prod.name });
            }
          }
          items.sort((a, b) => a.label.localeCompare(b.label));
          setOptions(items);
        } else {
          const data = await api.getCategoriesDetailed({
            start_date: startDate || undefined,
            end_date: endDate || undefined,
          });
          const items: OptionItem[] = data
            .map((m: { macro: string; total_conversations: number }) => ({
              label: `${m.macro} (${m.total_conversations} conv.)`,
              value: m.macro,
            }))
            .sort((a: OptionItem, b: OptionItem) => a.label.localeCompare(b.label));
          setOptions(items);
        }
      } catch (err) {
        console.error('Failed to load options:', err);
        setOptions([]);
      } finally {
        setLoading(false);
      }
    };

    fetchOptions();
  }, [dimension, startDate, endDate]);

  const handleDownload = async (format: 'md' | 'csv') => {
    if (!selectedValue) return;
    setDownloading(format);
    try {
      if (format === 'md') {
        await api.downloadDimensionMarkdown(dimension, selectedValue, startDate, endDate);
      } else {
        await api.downloadDimensionCsv(dimension, selectedValue, startDate, endDate);
      }
    } catch (err) {
      console.error('Download failed:', err);
    } finally {
      setDownloading(null);
    }
  };

  return (
    <div className="max-w-2xl mx-auto">
      <Card>
        <CardHeader>
          <CardTitle className="text-lg">Descargar Reporte Detallado</CardTitle>
          <p className="text-sm text-gray-500 mt-1">
            Selecciona un producto o una macro-categoria para generar un reporte con KPIs, tematicas,
            fallos, redirecciones y utilidad. Se descarga un Markdown con el analisis y un CSV con las conversaciones.
          </p>
        </CardHeader>
        <CardContent className="space-y-6">
          {/* Dimension toggle */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Tipo de reporte</label>
            <div className="flex gap-2">
              <button
                onClick={() => setDimension('product')}
                className={`flex-1 px-4 py-2.5 rounded-lg text-sm font-medium border transition-colors ${
                  dimension === 'product'
                    ? 'bg-teal-50 border-teal-300 text-teal-800'
                    : 'bg-white border-gray-200 text-gray-600 hover:bg-gray-50'
                }`}
              >
                Por Producto
              </button>
              <button
                onClick={() => setDimension('category')}
                className={`flex-1 px-4 py-2.5 rounded-lg text-sm font-medium border transition-colors ${
                  dimension === 'category'
                    ? 'bg-violet-50 border-violet-300 text-violet-800'
                    : 'bg-white border-gray-200 text-gray-600 hover:bg-gray-50'
                }`}
              >
                Por Categoria
              </button>
            </div>
          </div>

          {/* Selector */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              {dimension === 'product' ? 'Producto' : 'Macro-categoria'}
            </label>
            {loading ? (
              <div className="flex items-center gap-2 text-gray-400 text-sm py-2">
                <Loader2 size={16} className="animate-spin" /> Cargando opciones...
              </div>
            ) : (
              <select
                value={selectedValue}
                onChange={(e) => setSelectedValue(e.target.value)}
                className="w-full px-3 py-2.5 border border-gray-200 rounded-lg text-sm bg-white focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none"
              >
                <option value="">-- Seleccionar --</option>
                {options.map((opt) => (
                  <option key={opt.value} value={opt.value}>
                    {opt.label}
                  </option>
                ))}
              </select>
            )}
          </div>

          {/* Download buttons */}
          <div className="flex gap-3">
            <button
              onClick={() => handleDownload('md')}
              disabled={!selectedValue || downloading !== null}
              className="flex-1 flex items-center justify-center gap-2 px-4 py-2.5 bg-gray-700 hover:bg-gray-800 text-white rounded-lg text-sm font-medium transition-colors disabled:opacity-40 disabled:cursor-not-allowed"
            >
              {downloading === 'md' ? (
                <Loader2 size={16} className="animate-spin" />
              ) : (
                <FileText size={16} />
              )}
              Descargar Markdown
            </button>
            <button
              onClick={() => handleDownload('csv')}
              disabled={!selectedValue || downloading !== null}
              className="flex-1 flex items-center justify-center gap-2 px-4 py-2.5 bg-emerald-600 hover:bg-emerald-700 text-white rounded-lg text-sm font-medium transition-colors disabled:opacity-40 disabled:cursor-not-allowed"
            >
              {downloading === 'csv' ? (
                <Loader2 size={16} className="animate-spin" />
              ) : (
                <Table size={16} />
              )}
              Descargar CSV
            </button>
          </div>

          {selectedValue && (
            <p className="text-xs text-gray-400 text-center">
              El Markdown contiene el analisis detallado. El CSV contiene todas las conversaciones con indicadores por hilo.
            </p>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
