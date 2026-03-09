import React, { useState } from 'react';
import { Database, Zap, RefreshCw, CheckCircle, AlertCircle, TrendingUp, DollarSign } from 'lucide-react';
import axios from 'axios';

interface IngestReport {
  total_records: number;
  human_messages: number;
  ai_messages: number;
  categorized_total: number;
  needs_review: number;
  duration_seconds: number;
  ai_usage: {
    total_calls: number;
    input_tokens: number;
    output_tokens: number;
    estimated_cost_usd: number;
    estimated_cost_cop: number;
  };
}

const AdminPanel: React.FC = () => {
  const [loading, setLoading] = useState(false);
  const [report, setReport] = useState<IngestReport | null>(null);
  const [error, setError] = useState<string | null>(null);

  const triggerIngest = async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await axios.post('http://localhost:8000/api/admin/ingest');
      if (response.data.status === 'success') {
        setReport(response.data.report);
      } else {
        setError('Error en la ingesta: ' + response.data.message);
      }
    } catch (err: unknown) {
      if (err instanceof Error) {
        setError((err as any).response?.data?.detail || err.message || 'Error de conexión con el servidor');
      } else {
        setError('Error desconocido');
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between mb-4">
        <div>
          <h2 className="text-2xl font-bold text-white flex items-center gap-2">
            <Database className="text-indigo-400" />
            Administración de Datos
          </h2>
          <p className="text-slate-400">Control de ingesta y monitoreo de IA</p>
        </div>
        
        <button
          onClick={triggerIngest}
          disabled={loading}
          className={`flex items-center gap-2 px-6 py-3 rounded-xl font-semibold transition-all shadow-lg ${
            loading 
              ? 'bg-slate-700 text-slate-400 cursor-not-allowed' 
              : 'bg-indigo-600 hover:bg-indigo-500 text-white hover:scale-105 active:scale-95'
          }`}
        >
          {loading ? (
            <RefreshCw className="animate-spin" size={20} />
          ) : (
            <Zap size={20} />
          )}
          {loading ? 'Procesando Datos...' : 'Iniciar Ingesta Completa'}
        </button>
      </div>

      {error && (
        <div className="bg-red-500/10 border border-red-500/20 text-red-400 p-4 rounded-xl flex items-center gap-3">
          <AlertCircle size={20} />
          <p>{error}</p>
        </div>
      )}

      {report && !loading && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 transition-all animate-in fade-in slide-in-from-bottom-4">
          {/* General Stats */}
          <div className="bg-slate-800/50 backdrop-blur-md border border-slate-700/50 p-6 rounded-2xl shadow-xl">
            <div className="flex items-center gap-3 mb-4 text-indigo-400">
              <Database size={20} />
              <h3 className="font-semibold">Resumen de Ingesta</h3>
            </div>
            <div className="space-y-4">
              <div className="flex justify-between items-center">
                <span className="text-slate-400">Total Mensajes</span>
                <span className="text-2xl font-bold text-white">{report.total_records.toLocaleString()}</span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-slate-400 text-sm">Humanos / IA</span>
                <span className="text-slate-300">{report.human_messages} / {report.ai_messages}</span>
              </div>
              <div className="pt-2 border-t border-slate-700/50">
                <div className="flex justify-between items-center text-emerald-400 font-medium">
                  <span>Clasificados OK</span>
                  <span>{report.categorized_total}</span>
                </div>
                <div className="flex justify-between items-center text-amber-400 font-medium">
                  <span>Pendientes</span>
                  <span>{report.needs_review}</span>
                </div>
              </div>
            </div>
          </div>

          {/* AI Usage */}
          <div className="bg-slate-800/50 backdrop-blur-md border border-slate-700/50 p-6 rounded-2xl shadow-xl">
            <div className="flex items-center gap-3 mb-4 text-purple-400">
              <Zap size={20} />
              <h3 className="font-semibold">Consumo Gemini 1.5 Flash</h3>
            </div>
            <div className="space-y-4">
              <div className="flex justify-between items-center">
                <span className="text-slate-400">Llamadas a la API</span>
                <span className="text-2xl font-bold text-white">{report.ai_usage.total_calls}</span>
              </div>
              <div className="text-xs text-slate-500 flex justify-between">
                <span>Tokens In: {report.ai_usage.input_tokens.toLocaleString()}</span>
                <span>Tokens Out: {report.ai_usage.output_tokens.toLocaleString()}</span>
              </div>
              <div className="pt-2 border-t border-slate-700/50">
                <div className="flex justify-between items-center text-white">
                  <span className="flex items-center gap-1"><DollarSign size={14} /> Costo USD</span>
                  <span className="font-bold">${report.ai_usage.estimated_cost_usd.toFixed(4)}</span>
                </div>
                <div className="flex justify-between items-center text-indigo-300 italic text-sm">
                  <span>Costo en COP (aprox)</span>
                  <span>${report.ai_usage.estimated_cost_cop.toLocaleString()}</span>
                </div>
              </div>
            </div>
          </div>

          {/* Performance */}
          <div className="bg-slate-800/50 backdrop-blur-md border border-slate-700/50 p-6 rounded-2xl shadow-xl">
            <div className="flex items-center gap-3 mb-4 text-amber-400">
              <TrendingUp size={20} />
              <h3 className="font-semibold">Rendimiento</h3>
            </div>
            <div className="flex flex-col justify-center h-24 text-center">
              <span className="text-slate-400 text-sm mb-1">Tiempo de Procesamiento</span>
              <span className="text-3xl font-bold text-white">{report.duration_seconds}s</span>
            </div>
            <div className="mt-4 flex items-center gap-2 text-emerald-400 text-sm justify-center bg-emerald-500/10 py-2 rounded-lg">
              <CheckCircle size={14} />
              Ingesta Exitosa
            </div>
          </div>
        </div>
      )}

      {loading && (
        <div className="flex flex-col items-center justify-center p-20 space-y-4">
          <RefreshCw className="animate-spin text-indigo-500" size={48} />
          <p className="text-slate-400 animate-pulse font-medium">
            Procesando miles de hilos y clasificando con IA...
          </p>
          <p className="text-xs text-slate-600">Este proceso puede tardar hasta 2 minutos dependiendo del volumen de datos.</p>
        </div>
      )}

      {!report && !loading && (
        <div className="bg-slate-800/30 border border-dashed border-slate-700 p-12 rounded-3xl text-center">
          <div className="mx-auto w-16 h-16 bg-slate-800 rounded-full flex items-center justify-center mb-4 text-slate-500 border border-slate-700">
            <Database size={32} />
          </div>
          <h3 className="text-slate-300 font-medium text-lg">Inicia la ingesta de datos</h3>
          <p className="text-slate-500 max-w-sm mx-auto mt-2">
            Presiona el botón superior para sincronizar el CSV local con la base de datos SQLite y aplicar clasificación semántica mediante IA.
          </p>
        </div>
      )}
    </div>
  );
};

export default AdminPanel;
