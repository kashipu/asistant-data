
import { useEffect, useState } from 'react';
import { api } from './services/api';
import { KPIs } from './components/KPIs';
import { Charts } from './components/Charts';
import { MessageExplorer } from './components/MessageExplorer';
import { Referrals } from './components/Referrals';
import { Failures } from './components/Failures';
import { Insights } from './components/Insights';
import { UncategorizedPanel } from './components/UncategorizedPanel';
import { SummaryTable } from './components/SummaryTable';
import { SurveyPanel } from './components/SurveyPanel';
import { AdvisorPanel } from './components/AdvisorPanel';
import { DateRangePicker } from './components/DateRangePicker';
import { LayoutDashboard, MessageSquare, AlertOctagon, PhoneCall, FileQuestion, Activity, BarChart3, HelpCircle, UserCheck } from 'lucide-react';

function App() {
  const [activeTab, setActiveTab] = useState('dashboard');
  const [threadIdToNavigate, setThreadIdToNavigate] = useState<string | null>(null);
  const [kpiData, setKpiData] = useState<any>(null);
  const [loadingKpis, setLoadingKpis] = useState(true);

  // Global Date State
  const [startDate, setStartDate] = useState('');
  const [endDate, setEndDate] = useState('');

  const navigateToThread = (threadId: string) => {
    setThreadIdToNavigate(threadId);
    setActiveTab('messages');
  };

  useEffect(() => {
    const fetchKpis = async () => {
      setLoadingKpis(true);
      try {
        // Only fetching KPIs. Note: KPIs endpoint might not support date filtering yet in backend
        // but we should check or update it. For now, assuming it returns total stats.
        // If we want KPIs to respect dates, we need to update backend/main.py get_kpis_endpoint
        const data = await api.getKpis(); 
        setKpiData(data);
      } catch (error) {
        console.error(error);
      } finally {
        setLoadingKpis(false);
      }
    };
    fetchKpis();
  }, [activeTab]); // Refresh when changing tabs? Or just once? Let's refresh on tab change to keep it fresh.

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
      case 'surveys':
        return <SurveyPanel onNavigateToThread={navigateToThread} startDate={startDate} endDate={endDate} />;
      case 'messages':
        return <MessageExplorer initialThreadId={threadIdToNavigate || undefined} startDate={startDate} endDate={endDate} />;
      case 'insights':
        return <Insights />;
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
            onClick={() => setActiveTab('insights')}
            className={`w-full flex items-center gap-3 px-4 py-3 text-sm font-medium rounded-lg transition-colors ${activeTab === 'insights' ? 'bg-purple-50 text-purple-700' : 'text-gray-600 hover:bg-gray-50'}`}
          >
            <Activity size={18} /> Insights
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
                </h2>
                <p className="text-gray-500 text-sm mt-1">Última actualización: {new Date().toLocaleDateString()}</p>
             </div>
        </header>
        
        {renderContent()}
      </main>
    </div>
  );
}

export default App;
