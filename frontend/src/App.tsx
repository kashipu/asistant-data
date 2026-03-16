
import { useEffect, useState } from 'react';
import { api } from './services/api';
import { Charts } from './components/Charts';
import { MessageExplorer } from './components/MessageExplorer';
import { ReviewPanel } from './components/ReviewPanel';
import { FaqsPanel } from './components/FaqsPanel';
import { GapsPanel } from './components/GapsPanel';
import { KpisPanel } from './components/KpisPanel';
import { CategoriesDeepPanel } from './components/CategoriesDeepPanel';
import { ProductsDeepPanel } from './components/ProductsDeepPanel';
import { FailuresDeepPanel } from './components/FailuresDeepPanel';
import { LayoutDashboard, Activity, Ban, SearchCode, Bookmark, RefreshCw, Loader2, DatabaseZap, CheckCircle2, XCircle, TrendingUp, Layers, Package, BugPlay, MessageSquare, FileDown } from 'lucide-react';

function App() {
  const [activeTab, setActiveTab] = useState('dashboard');
  const [threadIdToNavigate, setThreadIdToNavigate] = useState<string | null>(null);

  const [startDate] = useState('');
  const [endDate] = useState('');
  const [isReprocessing, setIsReprocessing] = useState(false);
  const [etlElapsed, setEtlElapsed] = useState(0);
  const [etlFinished, setEtlFinished] = useState<'success' | 'error' | null>(null);
  const [dataPeriod, setDataPeriod] = useState<{ start: string | null, end: string | null }>({ start: null, end: null });

  // Fetch data period
  const fetchDataPeriod = async () => {
    try {
      const period = await api.getDataPeriod();
      setDataPeriod(period);
    } catch (err) {
      console.error("Failed to fetch data period:", err);
    }
  };

  useEffect(() => {
    fetchDataPeriod();
  }, []);

  // Check initial ETL status and setup polling only if active
  useEffect(() => {
    const checkStatus = async () => {
      try {
        const status = await api.getEtlStatus();

        // If it was running and stopped, trigger finish logic
        if (isReprocessing && !status.is_running) {
          const result = status.last_status === 'error' ? 'error' : 'success';
          setEtlFinished(result);
          setIsReprocessing(false);
          // Reload data period after success
          fetchDataPeriod();
          // Reload after 3s to let the user see the result
          setTimeout(() => window.location.reload(), 3000);
          return;
        }

        // Keep local state in sync
        if (status.is_running !== isReprocessing) {
          setIsReprocessing(status.is_running);
        }
        setEtlElapsed(status.elapsed_seconds || 0);
      } catch (err) {
        console.error("Failed to check ETL status:", err);
      }
    };

    // Initial check on mount
    if (!isReprocessing) {
        checkStatus();
    }

    // Only set interval if we are active
    let interval: number | undefined;
    if (isReprocessing) {
        interval = window.setInterval(checkStatus, 3000);
    }

    return () => {
        if (interval) clearInterval(interval);
    };
  }, [isReprocessing]);

  const handleReprocess = async () => {
    if (!window.confirm("¿Seguro que deseas volver a procesar y clasificar todos los datos? Esto tomará unos minutos y aplicará tus cambios del YAML y Etiquetas.")) return;

    setIsReprocessing(true);
    setEtlElapsed(0);
    try {
      await api.runEtl();
    } catch (error) {
      console.error(error);
      alert("Ocurrió un error al intentar iniciar el reprocesamiento.");
      setIsReprocessing(false);
    }
  };

  const navigateToThread = (threadId: string) => {
    setThreadIdToNavigate(threadId);
    setActiveTab('messages');
  };


  const renderContent = () => {
    switch (activeTab) {
      case 'dashboard':
        return <Charts startDate={startDate} endDate={endDate} />;
      case 'gaps':
        return <GapsPanel onNavigateToThread={navigateToThread} startDate={startDate} endDate={endDate} />;
      case 'kpis':
        return <KpisPanel startDate={startDate} endDate={endDate} />;
      case 'categories-deep':
        return <CategoriesDeepPanel onNavigateToThread={navigateToThread} startDate={startDate} endDate={endDate} />;
      case 'products-deep':
        return <ProductsDeepPanel onNavigateToThread={navigateToThread} startDate={startDate} endDate={endDate} />;
      case 'failures-deep':
        return <FailuresDeepPanel onNavigateToThread={navigateToThread} startDate={startDate} endDate={endDate} />;
      case 'feedbacks':
        return <ReviewPanel onNavigateToThread={navigateToThread} />;
      case 'faqs':
        return <FaqsPanel />;
      case 'messages':
        return <MessageExplorer initialThreadId={threadIdToNavigate || undefined} startDate={startDate} endDate={endDate} />;
      default:
        return <Charts startDate={startDate} endDate={endDate} />;
    }
  };

  return (
    <div className="flex h-screen bg-gray-50">
      {/* Sidebar */}
      <div className="w-64 bg-white border-r border-gray-200 flex flex-col">
        <div className="p-6 border-b border-gray-200">
          <h1 className="text-xl font-bold text-gray-800 flex items-center gap-2">
            <Activity className="text-blue-600" />
            Analytics
          </h1>
          <p className="text-xs text-gray-500 mt-1">Chatbot Dashboard</p>
        </div>

        <nav className="flex-1 p-4 space-y-1 overflow-y-auto">
          <div className="pb-2 px-4 text-xs font-semibold text-gray-400 uppercase tracking-wider">
            Informes
          </div>

          <button
            onClick={() => setActiveTab('dashboard')}
            className={`w-full flex items-center gap-3 px-4 py-3 text-sm font-medium rounded-lg transition-colors ${activeTab === 'dashboard' ? 'bg-blue-50 text-blue-700' : 'text-gray-600 hover:bg-gray-50'}`}
          >
            <LayoutDashboard size={18} /> Dashboard
          </button>

          <button
            onClick={() => setActiveTab('gaps')}
            className={`w-full flex items-center gap-3 px-4 py-3 text-sm font-medium rounded-lg transition-colors ${activeTab === 'gaps' ? 'bg-rose-50 text-rose-700' : 'text-gray-600 hover:bg-gray-50'}`}
          >
            <Ban size={18} /> Gaps y Redirecciones
          </button>

          <button
            onClick={() => setActiveTab('kpis')}
            className={`w-full flex items-center gap-3 px-4 py-3 text-sm font-medium rounded-lg transition-colors ${activeTab === 'kpis' ? 'bg-teal-50 text-teal-700' : 'text-gray-600 hover:bg-gray-50'}`}
          >
            <TrendingUp size={18} /> KPIs Explicados
          </button>

          <button
            onClick={() => setActiveTab('categories-deep')}
            className={`w-full flex items-center gap-3 px-4 py-3 text-sm font-medium rounded-lg transition-colors ${activeTab === 'categories-deep' ? 'bg-violet-50 text-violet-700' : 'text-gray-600 hover:bg-gray-50'}`}
          >
            <Layers size={18} /> Categorías Profundo
          </button>

          <button
            onClick={() => setActiveTab('products-deep')}
            className={`w-full flex items-center gap-3 px-4 py-3 text-sm font-medium rounded-lg transition-colors ${activeTab === 'products-deep' ? 'bg-teal-50 text-teal-700' : 'text-gray-600 hover:bg-gray-50'}`}
          >
            <Package size={18} /> Productos Profundo
          </button>

          <button
            onClick={() => setActiveTab('failures-deep')}
            className={`w-full flex items-center gap-3 px-4 py-3 text-sm font-medium rounded-lg transition-colors ${activeTab === 'failures-deep' ? 'bg-orange-50 text-orange-700' : 'text-gray-600 hover:bg-gray-50'}`}
          >
            <BugPlay size={18} /> Fallos Profundo
          </button>

          <div className="pt-4 pb-2 px-4 text-xs font-semibold text-gray-400 uppercase tracking-wider">
            Herramientas
          </div>

          <button
            onClick={() => setActiveTab('feedbacks')}
            className={`w-full flex items-center gap-3 px-4 py-3 text-sm font-medium rounded-lg transition-colors ${activeTab === 'feedbacks' ? 'bg-orange-50 text-orange-700' : 'text-gray-600 hover:bg-gray-50'}`}
          >
            <SearchCode size={18} /> Etiquetado (HITL)
          </button>

          <button
            onClick={() => setActiveTab('faqs')}
            className={`w-full flex items-center gap-3 px-4 py-3 text-sm font-medium rounded-lg transition-colors ${activeTab === 'faqs' ? 'bg-indigo-50 text-indigo-700' : 'text-gray-600 hover:bg-gray-50'}`}
          >
            <Bookmark size={18} /> Casos de Prueba (FAQ)
          </button>

          <button
            onClick={() => setActiveTab('messages')}
            className={`w-full flex items-center gap-3 px-4 py-3 text-sm font-medium rounded-lg transition-colors ${activeTab === 'messages' ? 'bg-blue-50 text-blue-700' : 'text-gray-600 hover:bg-gray-50'}`}
          >
            <MessageSquare size={18} /> Explorador de Mensajes
          </button>
        </nav>
      </div>

      {/* Main Content */}
      <main className="flex-1 p-8 overflow-y-auto h-screen">
        <header className="mb-8 flex justify-between items-center">
             <div>
                <h2 className="text-2xl font-bold text-gray-900">
                    {activeTab === 'dashboard' && 'Resumen General'}
                    {activeTab === 'gaps' && 'Vacíos de Conocimiento y Canales'}
                    {activeTab === 'kpis' && 'KPIs con Metodología'}
                    {activeTab === 'categories-deep' && 'Categorías — Análisis Profundo'}
                    {activeTab === 'products-deep' && 'Productos — Análisis Profundo'}
                    {activeTab === 'failures-deep' && 'Fallos — Análisis Profundo'}
                    {activeTab === 'feedbacks' && 'Human In The Loop (Entrenamiento)'}
                    {activeTab === 'faqs' && 'Casos de Prueba Frecuentes'}
                    {activeTab === 'messages' && 'Explorador de Conversaciones'}
                </h2>
                <div className="flex items-center gap-2 text-gray-500 text-sm mt-1">
                    <span className="font-medium">Periodo de datos:</span>
                    {dataPeriod.start && dataPeriod.end ? (
                        <span className="bg-blue-50 text-blue-700 px-2 py-0.5 rounded-md font-bold text-xs border border-blue-100">
                            {new Date(dataPeriod.start).toLocaleDateString('es-ES', { day: 'numeric', month: 'short' })} - {new Date(dataPeriod.end).toLocaleDateString('es-ES', { day: 'numeric', month: 'short', year: 'numeric' })}
                        </span>
                    ) : (
                        <span>Cargando...</span>
                    )}
                    <span className="mx-2 opacity-30">|</span>
                    <span>Hoy: {new Date().toLocaleDateString('es-ES')}</span>
                </div>
             </div>
             <div className="flex items-center gap-2">
                <button
                  onClick={() => api.downloadMarkdownReport({ startDate: startDate || undefined, endDate: endDate || undefined, full: true })}
                  className="flex items-center gap-2 px-4 py-2 bg-gray-600 hover:bg-gray-700 text-white rounded-lg text-sm font-medium transition-colors shadow-sm"
                >
                  <FileDown className="w-4 h-4" /> Descargar Informe
                </button>
                <button
                  onClick={handleReprocess}
                  disabled={isReprocessing}
                  className="flex items-center gap-2 px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg text-sm font-medium transition-colors shadow-sm disabled:opacity-50"
                >
                  {isReprocessing ? <Loader2 className="w-4 h-4 animate-spin" /> : <RefreshCw className="w-4 h-4" />}
                  {isReprocessing ? 'Procesando...' : 'Re-procesar Datos'}
                </button>
             </div>
        </header>

        {isReprocessing && (
          <div className="mb-6 bg-blue-50 border border-blue-200 rounded-xl p-4 flex items-center justify-between shadow-sm animate-pulse">
            <div className="flex items-center gap-3">
              <div className="bg-blue-100 p-2 rounded-full text-blue-600">
                <DatabaseZap className="w-5 h-5" />
              </div>
              <div>
                <h3 className="font-semibold text-blue-900">Actualizando Modelo NLP...</h3>
                <p className="text-sm text-blue-700">Extrayendo, transformando y re-clasificando miles de mensajes contra el motor YAML.</p>
              </div>
            </div>
            <div className="text-right">
              <div className="text-2xl font-mono font-bold text-blue-800">
                {Math.floor(etlElapsed / 60).toString().padStart(2, '0')}:{(etlElapsed % 60).toString().padStart(2, '0')}
              </div>
              <p className="text-xs font-medium text-blue-600 uppercase">Tiempo Transcurrido</p>
            </div>
          </div>
        )}

        {etlFinished === 'success' && (
          <div className="mb-6 bg-green-50 border border-green-200 rounded-xl p-4 flex items-center gap-3 shadow-sm">
            <CheckCircle2 className="w-6 h-6 text-green-600 shrink-0" />
            <div>
              <h3 className="font-semibold text-green-900">¡Reprocesamiento completado!</h3>
              <p className="text-sm text-green-700">Los datos se actualizaron correctamente. Recargando el tablero...</p>
            </div>
          </div>
        )}

        {etlFinished === 'error' && (
          <div className="mb-6 bg-red-50 border border-red-200 rounded-xl p-4 flex items-center gap-3 shadow-sm">
            <XCircle className="w-6 h-6 text-red-600 shrink-0" />
            <div>
              <h3 className="font-semibold text-red-900">Error en el reprocesamiento</h3>
              <p className="text-sm text-red-700">El proceso falló. Revisa los logs del servidor. El tablero se recargará en unos segundos.</p>
            </div>
          </div>
        )}

        {renderContent()}
      </main>
    </div>
  );
}

export default App;
