import { useState, useEffect } from 'react';
import { api } from '../services/api';
import { Loader2, RefreshCw, Send, AlertTriangle, Tag, Package, SmilePlus } from 'lucide-react';

interface FeedbackMessage {
  id: string;
  text: string;
  fecha: string;
  thread_id: string;
  sentiment?: string;
  categoria_yaml?: string;
  macro_yaml?: string;
  product_yaml?: string;
  product_macro_yaml?: string;
}

interface FeedbackOptions {
  categories: string[];
  products: string[];
  sentiments: string[];
}

interface FormState {
  category: string;
  sentiment: string;
  product: string;
}

const SENTIMENT_COLORS: Record<string, string> = {
  positivo: 'bg-green-100 text-green-700',
  neutral:  'bg-gray-100 text-gray-600',
  negativo: 'bg-red-100 text-red-700',
};

function CurrentBadge({ label, value, color }: { label: string; value?: string; color: string }) {
  if (!value) return null;
  return (
    <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded text-xs font-medium ${color}`}>
      {label}: {value}
    </span>
  );
}

export function ReviewPanel({ onNavigateToThread }: { onNavigateToThread?: (id: string) => void }) {
  const [messages, setMessages] = useState<FeedbackMessage[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [options, setOptions] = useState<FeedbackOptions>({ categories: [], products: [], sentiments: [] });
  const [formStates, setFormStates] = useState<Record<string, FormState>>({});
  const [submitting, setSubmitting] = useState<Record<string, boolean>>({});

  const limit = 20;

  useEffect(() => {
    const fetchData = async () => {
      setLoading(true);
      setError(null);
      try {
        const data = await api.getFeedbacks(page, limit);
        setMessages(data.data);
        setTotal(data.total);
        const newStates: Record<string, FormState> = {};
        data.data.forEach((m: FeedbackMessage) => {
          newStates[m.id] = {
            category: m.categoria_yaml || '',
            sentiment: m.sentiment || 'neutral',
            product: m.product_yaml || '',
          };
        });
        setFormStates(newStates);
      } catch (err) {
        console.error(err);
        setError('No se pudo conectar con el servidor.');
      } finally {
        setLoading(false);
      }
    };
    fetchData();
    api.getFeedbackOptions().then((data: FeedbackOptions) => setOptions(data));
  }, [page]);

  const handleUpdate = (id: string, field: keyof FormState, value: string) => {
    setFormStates(prev => ({ ...prev, [id]: { ...prev[id], [field]: value } }));
  };

  const handleSubmit = async (message: FeedbackMessage) => {
    const form = formStates[message.id];
    // Use the pre-filled category from the message if the user didn't change it
    const categoryToSave = form.category || message.categoria_yaml || '';
    if (!categoryToSave) {
      alert('Por favor selecciona una categoría.');
      return;
    }
    setSubmitting(prev => ({ ...prev, [message.id]: true }));
    try {
      await api.categorizeFeedback({
        message_id: message.id,
        new_category: categoryToSave,
        new_sentiment: form.sentiment || undefined,
        new_product: form.product || undefined,
        original_text: message.text,
      });
      setMessages(prev => prev.filter(m => m.id !== message.id));
      setTotal(t => t - 1);
    } catch (err) {
      console.error(err);
      alert('Error guardando la retroalimentación.');
    } finally {
      setSubmitting(prev => ({ ...prev, [message.id]: false }));
    }
  };

  return (
    <div className="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden">
      {/* Header */}
      <div className="p-6 border-b border-gray-100 flex justify-between items-center bg-gradient-to-r from-orange-50 to-white">
        <div>
          <h2 className="text-xl font-bold text-gray-800 flex items-center gap-2">
            <AlertTriangle className="text-orange-500" />
            Human in the Loop (HITL) — Etiquetado Manual
          </h2>
          <p className="text-sm text-gray-500 mt-1">
            Revisa los mensajes que el NLP no reconoció. Al categorizarlos, el modelo{' '}
            <b>aprenderá</b> y actualizará <code>categorias.yml</code>.
          </p>
        </div>
        <div className="bg-white px-4 py-2 rounded-lg border shadow-sm text-center">
          <span className="text-2xl font-bold text-orange-600">{total}</span>
          <p className="text-xs text-gray-500 uppercase font-semibold">Pendientes</p>
        </div>
      </div>

      {/* Table */}
      <div className="p-0">
        {loading && messages.length === 0 ? (
          <div className="flex justify-center items-center h-64 text-gray-500">
            <Loader2 className="w-8 h-8 animate-spin" />
          </div>
        ) : error ? (
          <div className="flex flex-col items-center justify-center h-40 text-red-600 bg-red-50 gap-2 p-6">
            <AlertTriangle className="w-8 h-8" />
            <p className="text-sm font-medium">{error}</p>
          </div>
        ) : messages.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-64 text-gray-500 bg-gray-50">
            <div className="p-4 bg-green-100 text-green-700 rounded-full mb-4">
              <RefreshCw className="w-8 h-8" />
            </div>
            <p>¡Todo limpio! No hay mensajes pendientes de revisión.</p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200 text-sm">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider w-28">Fecha</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider w-64">Mensaje Original</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    <span className="flex items-center gap-1"><Tag className="w-3.5 h-3.5" /> Categoría</span>
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    <span className="flex items-center gap-1"><Package className="w-3.5 h-3.5" /> Producto</span>
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    <span className="flex items-center gap-1"><SmilePlus className="w-3.5 h-3.5" /> Sentimiento</span>
                  </th>
                  <th className="px-4 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider">Acción</th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {messages.map((msg) => {
                  const form = formStates[msg.id] || { category: '', sentiment: 'neutral', product: '' };
                  return (
                    <tr key={msg.id} className="hover:bg-orange-50/40 transition-colors align-top">
                      {/* Date + thread link */}
                      <td className="px-4 py-3 whitespace-nowrap">
                        <div className="font-medium text-gray-800">{msg.fecha}</div>
                        <button
                          onClick={() => onNavigateToThread && onNavigateToThread(msg.thread_id)}
                          className="text-xs text-blue-600 hover:underline mt-0.5 block"
                        >
                          Ver conversación
                        </button>
                        {/* Current state badges */}
                        <div className="flex flex-col gap-0.5 mt-1.5">
                          {msg.macro_yaml && (
                            <CurrentBadge label="Macro" value={msg.macro_yaml} color="bg-blue-50 text-blue-600" />
                          )}
                          {msg.product_macro_yaml && (
                            <CurrentBadge label="Prod" value={msg.product_macro_yaml} color="bg-purple-50 text-purple-600" />
                          )}
                          {msg.sentiment && (
                            <CurrentBadge label="" value={msg.sentiment} color={SENTIMENT_COLORS[msg.sentiment] ?? 'bg-gray-100 text-gray-600'} />
                          )}
                        </div>
                      </td>

                      {/* Message text */}
                      <td className="px-4 py-3 max-w-xs">
                        <div className="text-gray-800 break-words whitespace-pre-wrap line-clamp-4">{msg.text}</div>
                      </td>

                      {/* Category selector */}
                      <td className="px-4 py-3 whitespace-nowrap">
                        <div className="text-xs text-gray-400 mb-1">
                          Actual: <span className="text-gray-600">{msg.categoria_yaml || '—'}</span>
                        </div>
                        <input
                          type="text"
                          list={`cats-${msg.id}`}
                          placeholder="Selecciona o escribe..."
                          value={form.category}
                          onChange={(e) => handleUpdate(msg.id, 'category', e.target.value)}
                          className="w-48 text-sm border border-gray-300 rounded-md px-2 py-1 focus:border-orange-400 focus:ring-1 focus:ring-orange-300 outline-none"
                        />
                        <datalist id={`cats-${msg.id}`}>
                          {options.categories.map((opt, i) => (
                            <option key={i} value={opt} />
                          ))}
                        </datalist>
                      </td>

                      {/* Product selector */}
                      <td className="px-4 py-3 whitespace-nowrap">
                        <div className="text-xs text-gray-400 mb-1">
                          Actual: <span className="text-gray-600">{msg.product_yaml || '—'}</span>
                        </div>
                        <select
                          value={form.product}
                          onChange={(e) => handleUpdate(msg.id, 'product', e.target.value)}
                          className="w-44 text-sm border border-gray-300 rounded-md px-2 py-1 focus:border-orange-400 focus:ring-1 focus:ring-orange-300 outline-none"
                        >
                          <option value="">Sin cambio</option>
                          {options.products.map((p, i) => (
                            <option key={i} value={p}>{p}</option>
                          ))}
                        </select>
                      </td>

                      {/* Sentiment selector */}
                      <td className="px-4 py-3 whitespace-nowrap">
                        <div className="text-xs text-gray-400 mb-1">
                          Actual: <span className={`font-medium ${SENTIMENT_COLORS[msg.sentiment ?? '']?.split(' ')[1] ?? 'text-gray-600'}`}>{msg.sentiment || '—'}</span>
                        </div>
                        <select
                          value={form.sentiment}
                          onChange={(e) => handleUpdate(msg.id, 'sentiment', e.target.value)}
                          className="text-sm border border-gray-300 rounded-md px-2 py-1 focus:border-orange-400 focus:ring-1 focus:ring-orange-300 outline-none"
                        >
                          {options.sentiments.map((s, i) => (
                            <option key={i} value={s}>{s.charAt(0).toUpperCase() + s.slice(1)}</option>
                          ))}
                        </select>
                      </td>

                      {/* Submit */}
                      <td className="px-4 py-3 text-center whitespace-nowrap">
                        <button
                          onClick={() => handleSubmit(msg)}
                          disabled={submitting[msg.id]}
                          className={`inline-flex items-center gap-1.5 px-3 py-1.5 border border-transparent text-sm font-medium rounded-md shadow-sm text-white transition-colors ${
                            submitting[msg.id] ? 'bg-gray-400 cursor-not-allowed' : 'bg-orange-600 hover:bg-orange-700'
                          }`}
                        >
                          {submitting[msg.id]
                            ? <Loader2 className="w-4 h-4 animate-spin" />
                            : <Send className="w-4 h-4" />}
                          Guardar
                        </button>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Pagination */}
      {total > limit && (
        <div className="px-6 py-4 border-t border-gray-100 flex items-center justify-between bg-gray-50">
          <p className="text-sm text-gray-700">
            Mostrando{' '}
            <span className="font-medium">{(page - 1) * limit + 1}</span> a{' '}
            <span className="font-medium">{Math.min(page * limit, total)}</span> de{' '}
            <span className="font-medium">{total}</span>
          </p>
          <div className="flex gap-2">
            <button
              onClick={() => setPage(p => Math.max(1, p - 1))}
              disabled={page === 1}
              className="px-3 py-1 border rounded-md bg-white text-sm disabled:opacity-50"
            >
              Anterior
            </button>
            <button
              onClick={() => setPage(p => p + 1)}
              disabled={page * limit >= total}
              className="px-3 py-1 border rounded-md bg-white text-sm disabled:opacity-50"
            >
              Siguiente
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
