
import { useEffect, useState } from 'react';
import { api } from './services/api';
import { Charts } from './components/Charts';
import { MessageExplorer } from './components/MessageExplorer';
import { Referrals } from './components/Referrals';
import { Failures } from './components/Failures';
import { Insights } from './components/Insights';
import { UncategorizedPanel } from './components/UncategorizedPanel';
import { SummaryTable } from './components/SummaryTable';
import { SurveyPanel } from './components/SurveyPanel';
import { AdvisorPanel } from './components/AdvisorPanel';
import { ReviewPanel } from './components/ReviewPanel';
import { FaqsPanel } from './components/FaqsPanel';
import { QualitativeInsights } from './components/QualitativeInsights';
import { LayoutDashboard, MessageSquare, AlertOctagon, PhoneCall, Activity, BarChart3, HelpCircle, SearchCode, Bookmark, RefreshCw, Loader2, DatabaseZap, CheckCircle2, XCircle, Star } from 'lucide-react';

function App() {
  const [activeTab, setActiveTab] = useState('dashboard');
  const [threadIdToNavigate, setThreadIdToNavigate] = useState<string | null>(null);

  const [startDate] = useState('');
  const [endDate] = useState('');
  const [isReprocessing, setIsReprocessing] = useState(false);
  const [etlElapsed, setEtlElapsed] = useState(0);
  const [etlFinished, setEtlFinished] = useState<'success' | 'error' | null>(null);

  // Poll ETL status
  useEffect(() => {
    const checkStatus = async () => {
      try {
        const status = await api.getEtlStatus();

        if (isReprocessing && !status.is_running) {
          const result = status.last_status === 'error' ? 'error' : 'success';
          setEtlFinished(result);
          setIsReprocessing(false);
          // Reload after 3s so el usuario ve el resultado
          setTimeout(() => window.location.reload(), 3000);
          return;
        }

        setIsReprocessing(status.is_running);
        setEtlElapsed(status.elapsed_seconds || 0);
      } catch (err) {
        console.error("Failed to check ETL status:", err);
      }
    };

    checkStatus();
    const interval = setInterval(checkStatus, 3000);
    return () => clearInterval(interval);
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
      case 'categories':
        return <SummaryTable startDate={startDate} endDate={endDate} />;
      case 'failures':
        return <Failures onNavigateToThread={navigateToThread} startDate={startDate} endDate={endDate} />;
      case 'referrals':
        return <Referrals onNavigateToThread={navigateToThread} startDate={startDate} endDate={endDate} />;
      case 'uncategorized':
        return <UncategorizedPanel onNavigateToThread={navigateToThread} startDate={startDate} endDate={endDate} />;
      case 'advisors':
        return <AdvisorPanel onNavigateToThread={navigateToThread} startDate={startDate} endDate={endDate} />;
      case 'feedbacks':
        return <ReviewPanel onNavigateToThread={navigateToThread} />;
      case 'surveys':
        return <SurveyPanel onNavigateToThread={navigateToThread} startDate={startDate} endDate={endDate} />;
      case 'messages':
        return <MessageExplorer initialThreadId={threadIdToNavigate || undefined} startDate={startDate} endDate={endDate} />;
      case 'insights':
        return <Insights />;
      case 'qualitative':
        return <QualitativeInsights />;
      case 'faqs':
        return <FaqsPanel />;
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
          <button 
            onClick={() => setActiveTab('dashboard')}
            className={`w-full flex items-center gap-3 px-4 py-3 text-sm font-medium rounded-lg transition-colors ${activeTab === 'dashboard' ? 'bg-blue-50 text-blue-700' : 'text-gray-600 hover:bg-gray-50'}`}
          >
            <LayoutDashboard size={18} /> Dashboard
          </button>
          
          <div className="pt-4 pb-2 px-4 text-xs font-semibold text-gray-400 uppercase tracking-wider">
            Análisis
          </div>

          <button 
            onClick={() => setActiveTab('categories')}
            className={`w-full flex items-center gap-3 px-4 py-3 text-sm font-medium rounded-lg transition-colors ${activeTab === 'categories' ? 'bg-blue-50 text-blue-700' : 'text-gray-600 hover:bg-gray-50'}`}
          >
            <BarChart3 size={18} /> Categorías
          </button>

 
          <button 
            onClick={() => setActiveTab('surveys')}
            className={`w-full flex items-center gap-3 px-4 py-3 text-sm font-medium rounded-lg transition-colors ${activeTab === 'surveys' ? 'bg-blue-50 text-blue-700' : 'text-gray-600 hover:bg-gray-50'}`}
          >
            <HelpCircle size={18} /> Encuestas
          </button>

          <div className="pt-4 pb-2 px-4 text-xs font-semibold text-gray-400 uppercase tracking-wider">
            Monitorización
          </div>
          
          <button 
            onClick={() => setActiveTab('failures')}
            className={`w-full flex items-center gap-3 px-4 py-3 text-sm font-medium rounded-lg transition-colors ${activeTab === 'failures' ? 'bg-red-50 text-red-700' : 'text-gray-600 hover:bg-gray-50'}`}
          >
            <AlertOctagon size={18} /> Fallos
          </button>
          
          <button 
            onClick={() => setActiveTab('referrals')}
            className={`w-full flex items-center gap-3 px-4 py-3 text-sm font-medium rounded-lg transition-colors ${activeTab === 'referrals' ? 'bg-blue-50 text-blue-700' : 'text-gray-600 hover:bg-gray-50'}`}
          >
            <PhoneCall size={18} /> Servilínea
          </button>

          <div className="pt-4 pb-2 px-4 text-xs font-semibold text-gray-400 uppercase tracking-wider">
            Exploración
          </div>
          
          <button 
            onClick={() => setActiveTab('messages')}
            className={`w-full flex items-center gap-3 px-4 py-3 text-sm font-medium rounded-lg transition-colors ${activeTab === 'messages' ? 'bg-blue-50 text-blue-700' : 'text-gray-600 hover:bg-gray-50'}`}
          >
            <MessageSquare size={18} /> Mensajes
          </button>

          <button 
            onClick={() => setActiveTab('feedbacks')}
            className={`w-full flex items-center gap-3 px-4 py-3 text-sm font-medium rounded-lg transition-colors ${activeTab === 'feedbacks' ? 'bg-orange-50 text-orange-700' : 'text-gray-600 hover:bg-gray-50'}`}
          >
            <SearchCode size={18} /> Etiquetado (HITL)
          </button>

          <button 
            onClick={() => setActiveTab('insights')}
            className={`w-full flex items-center gap-3 px-4 py-3 text-sm font-medium rounded-lg transition-colors ${activeTab === 'insights' ? 'bg-purple-50 text-purple-700' : 'text-gray-600 hover:bg-gray-50'}`}
          >
            <Activity size={18} /> Insights
          </button>

          <button 
            onClick={() => setActiveTab('qualitative')}
            className={`w-full flex items-center gap-3 px-4 py-3 text-sm font-medium rounded-lg transition-colors ${activeTab === 'qualitative' ? 'bg-yellow-50 text-yellow-700' : 'text-gray-600 hover:bg-gray-50'}`}
          >
            <Star size={18} /> Insights Cualitativos
          </button>

          <button 
            onClick={() => setActiveTab('faqs')}
            className={`w-full flex items-center gap-3 px-4 py-3 text-sm font-medium rounded-lg transition-colors ${activeTab === 'faqs' ? 'bg-indigo-50 text-indigo-700' : 'text-gray-600 hover:bg-gray-50'}`}
          >
            <Bookmark size={18} /> Casos de Prueba (FAQ)
          </button>
        </nav>
      </div>

      {/* Main Content */}
      <main className="flex-1 p-8 overflow-y-auto h-screen">
        <header className="mb-8 flex justify-between items-center">
             <div>
                <h2 className="text-2xl font-bold text-gray-900">
                    {activeTab === 'dashboard' && 'Resumen General'}
                    {activeTab === 'messages' && 'Explorador de Conversaciones'}
                    {activeTab === 'failures' && 'Detección de Fallos'}
                    {activeTab === 'text' && 'Análisis de Contenido'}
                    {activeTab === 'insights' && 'Insights y Tendencias'}
                    {activeTab === 'uncategorized' && 'Conversaciones Sin Categoría'}
                    {activeTab === 'feedbacks' && 'Human In The Loop (Entrenamiento)'}
                    {activeTab === 'faqs' && 'Casos de Prueba Frecuentes'}
                </h2>
                <p className="text-gray-500 text-sm mt-1">Última actualización: {new Date().toLocaleDateString()}</p>
             </div>
             <div>
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
