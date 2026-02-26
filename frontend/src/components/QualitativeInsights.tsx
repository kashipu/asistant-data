import React, { useEffect, useState } from 'react';
import { api } from '../services/api';
import { MessageSquare, Users, Star, PhoneCall, PieChart, BarChart2, Hash, AlertTriangle, ClipboardCheck } from 'lucide-react';

interface QualitativeData {
  messages: {
    total: number;
    human: number;
    ai: number;
    human_pct: number;
    ai_pct: number;
  };
  conversations: {
    total: number;
  };
  peak_hours: Array<{ hour: number, count: number }>;
  summary: {
    top_categories: Array<{ name: string, count: number }>;
    top_sentiments: Array<{ name: string, pct: number }>;
    top_products: Array<{ name: string, count: number }>;
  };
  referrals: {
    total: number;
    pct: number;
  };
}

interface CategoryData {
  category_name: string;
  error?: string;
  messages: {
    total: number;
    human: number;
    human_pct: number;
  };
  frequent_messages: { text: string; count: number; thread_id?: string }[];
  frequent_messages_ai?: { text: string; count: number; thread_id?: string }[];
  distribution: {
    subcategories: Array<{ name: string, count: number }>;
    products: Array<{ name: string, count: number }>;
  };
  referrals: {
    total: number;
  };
}

interface SummaryRow {
  category: string;
  intention: string;
  product: string;
  unique_conversations: number;
  total_interactions: number;
  human_msgs: number;
  ai_msgs: number;
  tool_msgs: number;
  servilinea_referrals: number;
  positive: number;
  neutral: number;
  negative: number;
}

interface SurveyData {
  stats: {
    total: number;
    useful: number;
    not_useful: number;
  };
  conversations: {
    thread_id: string;
    date: string;
    feedback: string;
    status: string;
  }[];
}

interface GroupedCategoryRow {
  category: string;
  unique_conversations: number;
  total_interactions: number;
  human_msgs: number;
  ai_msgs: number;
  tool_msgs: number;
  servilinea_referrals: number;
  positive: number;
  neutral: number;
  negative: number;
}

export const QualitativeInsights: React.FC = () => {
  const [generalData, setGeneralData] = useState<QualitativeData | null>(null);
  const [summaryData, setSummaryData] = useState<SummaryRow[]>([]);
  const [surveyData, setSurveyData] = useState<SurveyData | null>(null);
  const [selectedCategory, setSelectedCategory] = useState<string>('');
  const [categoryData, setCategoryData] = useState<CategoryData | null>(null);
  
  const [loadingGeneral, setLoadingGeneral] = useState(true);
  const [loadingCategory, setLoadingCategory] = useState(false);

  // View toggle and sorting state
  const [activeTab, setActiveTab] = useState<'summary' | 'detailed'>('summary');
  const [sortConfigA, setSortConfigA] = useState<{ key: keyof GroupedCategoryRow | 'pct_global' | 'pct_referrals', direction: 'asc' | 'desc' } | null>(null);
  const [sortConfigB, setSortConfigB] = useState<{ key: keyof SummaryRow | 'pct_human' | 'pct_referrals', direction: 'asc' | 'desc' } | null>(null);

  // Grouped data for Table A
  const groupedByCategory = React.useMemo(() => {
    const map = new Map<string, GroupedCategoryRow>();
    summaryData.forEach(row => {
        if (!map.has(row.category)) {
            map.set(row.category, {
                category: row.category,
                unique_conversations: 0,
                total_interactions: 0,
                human_msgs: 0,
                ai_msgs: 0,
                tool_msgs: 0,
                servilinea_referrals: 0,
                positive: 0,
                neutral: 0,
                negative: 0
            });
        }
        const curr = map.get(row.category)!;
        curr.unique_conversations += row.unique_conversations;
        curr.total_interactions += row.total_interactions;
        curr.human_msgs += row.human_msgs;
        curr.ai_msgs += row.ai_msgs;
        curr.tool_msgs += row.tool_msgs;
        curr.servilinea_referrals += row.servilinea_referrals;
        curr.positive += row.positive;
        curr.neutral += row.neutral;
        curr.negative += row.negative;
    });
    return Array.from(map.values());
  }, [summaryData]);

  // Sorting logic for Table A
  const sortedGroupedData = React.useMemo(() => {
    const sortableItems = [...groupedByCategory];
    if (sortConfigA !== null) {
      sortableItems.sort((a, b) => {
        let aValue: number | string = a[sortConfigA.key as keyof GroupedCategoryRow];
        let bValue: number | string = b[sortConfigA.key as keyof GroupedCategoryRow];
        
        if (sortConfigA.key === 'pct_global') {
             aValue = a.unique_conversations;
             bValue = b.unique_conversations;
        } else if (sortConfigA.key === 'pct_referrals') {
             aValue = a.unique_conversations > 0 ? (a.servilinea_referrals / a.unique_conversations) : 0;
             bValue = b.unique_conversations > 0 ? (b.servilinea_referrals / b.unique_conversations) : 0;
        }

        if (aValue < bValue) return sortConfigA.direction === 'asc' ? -1 : 1;
        if (aValue > bValue) return sortConfigA.direction === 'asc' ? 1 : -1;
        return 0;
      });
    } else {
        // Default sort by conversations desc
        sortableItems.sort((a, b) => b.unique_conversations - a.unique_conversations);
    }
    return sortableItems;
  }, [groupedByCategory, sortConfigA]);

  // Calculate top subcategory directly from summaryData
  const topSubcategory = React.useMemo(() => {
    const map = new Map<string, number>();
    const excludedTerms = ['encuesta', 'uncategorized', 'sin intención clara', 'sin intencion clara', 'ninguno', 'none', 'nan'];
    
    summaryData.forEach(row => {
        if (!excludedTerms.includes(row.intention.toLowerCase())) {
            map.set(row.intention, (map.get(row.intention) || 0) + row.unique_conversations);
        }
    });
    let max = 0;
    let name = 'N/A';
    map.forEach((count, key) => {
        if(count > max) { max = count; name = key; }
    });
    return { name, count: max };
  }, [summaryData]);

  // Sorting logic for Table B
  const sortedDetailedData = React.useMemo(() => {
      const sortableItems = [...summaryData];
      if (sortConfigB !== null) {
        sortableItems.sort((a, b) => {
            let aValue: number | string = a[sortConfigB.key as keyof SummaryRow];
            let bValue: number | string = b[sortConfigB.key as keyof SummaryRow];

            if (sortConfigB.key === 'pct_human') {
                 const aTotal = a.human_msgs + a.ai_msgs + a.tool_msgs;
                 const bTotal = b.human_msgs + b.ai_msgs + b.tool_msgs;
                 aValue = aTotal > 0 ? (a.human_msgs / aTotal) : 0;
                 bValue = bTotal > 0 ? (b.human_msgs / bTotal) : 0;
            } else if (sortConfigB.key === 'pct_referrals') {
                 aValue = a.unique_conversations > 0 ? (a.servilinea_referrals / a.unique_conversations) : 0;
                 bValue = b.unique_conversations > 0 ? (b.servilinea_referrals / b.unique_conversations) : 0;
            }

            if (aValue < bValue) return sortConfigB.direction === 'asc' ? -1 : 1;
            if (aValue > bValue) return sortConfigB.direction === 'asc' ? 1 : -1;
            return 0;
        });
      } else {
          // Default sort by conversations desc
          sortableItems.sort((a, b) => b.unique_conversations - a.unique_conversations);
      }
      return sortableItems;
  }, [summaryData, sortConfigB]);

  const requestSortA = (key: keyof GroupedCategoryRow | 'pct_global' | 'pct_referrals') => {
    let direction: 'asc' | 'desc' = 'desc';
    if (sortConfigA && sortConfigA.key === key && sortConfigA.direction === 'desc') {
      direction = 'asc';
    }
    setSortConfigA({ key, direction });
  };

  const requestSortB = (key: keyof SummaryRow | 'pct_human' | 'pct_referrals') => {
    let direction: 'asc' | 'desc' = 'desc';
    if (sortConfigB && sortConfigB.key === key && sortConfigB.direction === 'desc') {
      direction = 'asc';
    }
    setSortConfigB({ key, direction });
  };

  useEffect(() => {
    const fetchInitial = async () => {
      try {
        const [qData, sData, srvData] = await Promise.all([
          api.getQualitativeInsights(),
          api.getSummary(),
          api.getSurveys()
        ]);
        setGeneralData(qData);
        setSummaryData(sData || []);
        setSurveyData(srvData);
      } catch (error) {
        console.error("Error fetching qualitative initial data:", error);
      } finally {
        setLoadingGeneral(false);
      }
    };
    fetchInitial();
  }, []);

  useEffect(() => {
    if (!selectedCategory) return;
    const fetchCategory = async () => {
      setLoadingCategory(true);
      try {
        const catData = await api.getCategoryInsights(selectedCategory);
        setCategoryData(catData);
      } catch (error) {
        console.error("Error fetching category info:", error);
      } finally {
        setLoadingCategory(false);
      }
    };
    fetchCategory();
  }, [selectedCategory]);

  if (loadingGeneral || !generalData) {
    return (
      <div className="p-8 flex justify-center items-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  return (
    <div className="space-y-8">
      
      {/* 100% Baseline Banner */}
      <div className="bg-gradient-to-r from-blue-600 to-indigo-700 rounded-2xl p-6 text-white shadow-md flex justify-between items-center bg-pattern">
          <div>
              <h2 className="text-2xl font-bold mb-1">Universo de Análisis</h2>
              <p className="text-blue-100 text-sm">Base referencial (100%) para el cálculo de todos los KPIs cualitativos.</p>
          </div>
          <div className="flex gap-8">
              <div className="text-right">
                  <div className="text-3xl font-extrabold">{generalData.conversations.total.toLocaleString()}</div>
                  <div className="text-blue-200 text-xs uppercase font-semibold tracking-wider">Conversaciones (100%)</div>
              </div>
              <div className="text-right">
                  <div className="text-3xl font-extrabold">{generalData.messages.total.toLocaleString()}</div>
                  <div className="text-blue-200 text-xs uppercase font-semibold tracking-wider">Mensajes (100%)</div>
              </div>
          </div>
      </div>
      
      {/* SECTION A: General Cards */}
      <div>
        <h2 className="text-xl font-bold text-gray-800 mb-4 flex items-center gap-2">
            <Star className="text-yellow-500 w-6 h-6"/> KPIs Cualitativos Generales
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4 mb-6">
            
            {/* Card 1: Mensajes Human */}
            <div className="bg-white p-5 rounded-xl shadow-sm border border-gray-100 flex flex-col justify-between">
                <div className="flex items-center gap-3 mb-2">
                    <div className="bg-blue-100 p-2 rounded-lg text-blue-600">
                        <MessageSquare className="w-5 h-5"/>
                    </div>
                    <span className="text-sm font-semibold text-gray-600">Mensajes Humanos</span>
                </div>
                <div>
                   <p className="text-2xl font-bold text-gray-900">{generalData.messages.human.toLocaleString()} <span className="text-sm font-normal text-gray-500">mensajes</span></p>
                   <p className="text-xs text-gray-500 mt-1">El {generalData.messages.human_pct}% del total</p>
                </div>
            </div>

            {/* Card 2: Mensajes IA */}
            <div className="bg-white p-5 rounded-xl shadow-sm border border-gray-100 flex flex-col justify-between">
                <div className="flex items-center gap-3 mb-2">
                    <div className="bg-indigo-100 p-2 rounded-lg text-indigo-600">
                        <MessageSquare className="w-5 h-5"/>
                    </div>
                    <span className="text-sm font-semibold text-gray-600">Mensajes IA</span>
                </div>
                <div>
                   <p className="text-2xl font-bold text-gray-900">{generalData.messages.ai.toLocaleString()} <span className="text-sm font-normal text-gray-500">mensajes</span></p>
                   <p className="text-xs text-gray-500 mt-1">El {generalData.messages.ai_pct}% del total</p>
                </div>
            </div>

            {/* Card 3: Conversaciones */}
            <div className="bg-white p-5 rounded-xl shadow-sm border border-gray-100 flex flex-col justify-between">
                <div className="flex items-center gap-3 mb-2">
                    <div className="bg-purple-100 p-2 rounded-lg text-purple-600">
                        <Users className="w-5 h-5"/>
                    </div>
                    <span className="text-sm font-semibold text-gray-600">Conversaciones</span>
                </div>
                <div>
                   <p className="text-3xl font-bold text-gray-900">{generalData.conversations.total.toLocaleString()}</p>
                   <p className="text-sm text-gray-500 mt-1">Conversaciones únicas</p>
                </div>
            </div>

            {/* Card 4: Traslados */}
            <div className="bg-white p-5 rounded-xl shadow-sm border border-gray-100 flex flex-col justify-between">
                <div className="flex items-center gap-3 mb-2">
                    <div className="bg-red-100 p-2 rounded-lg text-red-600">
                        <PhoneCall className="w-5 h-5"/>
                    </div>
                    <span className="text-sm font-semibold text-gray-600">Traslados</span>
                </div>
                <div>
                   <p className="text-2xl font-bold text-gray-900">{generalData.referrals.pct}% <span className="text-sm font-normal text-gray-500">Derivados</span></p>
                   <p className="text-xs text-gray-500 mt-1">{generalData.referrals.total.toLocaleString()} conversaciones</p>
                </div>
            </div>

            {/* Card 5: Utilidad Encuesta */}
            <div className="bg-white p-5 rounded-xl shadow-sm border border-gray-100 flex flex-col justify-between">
                <div className="flex items-center gap-3 mb-2">
                    <div className="bg-emerald-100 p-2 rounded-lg text-emerald-600">
                        <ClipboardCheck className="w-5 h-5"/>
                    </div>
                    <span className="text-sm font-semibold text-gray-600">Utilidad (Encuesta)</span>
                </div>
                <div>
                    <p className="text-2xl font-bold text-gray-900">
                        {surveyData ? Math.round((surveyData.stats.useful / (surveyData.stats.total || 1)) * 100) : 0}% <span className="text-sm font-normal text-gray-500">Positivo</span>
                    </p>
                    <p className="text-xs text-gray-500 mt-1">
                        Encuestados: {surveyData ? Math.round((surveyData.stats.total / generalData.conversations.total) * 100) : 0}% del total ({surveyData?.stats.total || 0} convos)
                    </p>
                    <p className="text-xs text-gray-400 mt-1 flex justify-between">
                        <span>Útil: {surveyData?.stats.useful || 0}</span>
                        <span>No Útil: {surveyData?.stats.not_useful || 0}</span>
                    </p>
                </div>
            </div>

        </div>

        <h2 className="text-lg font-bold text-gray-800 mb-4 flex items-center gap-2">
            <BarChart2 className="text-green-500 w-5 h-5"/> Top Consultas
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {/* Card 1: Top Categoria */}
            <div className="bg-white p-5 rounded-xl shadow-sm border border-gray-100 flex flex-col justify-between">
                <div className="flex items-center justify-between mb-2">
                    <span className="text-xs font-bold text-gray-400 uppercase tracking-wider">Categoría más consultada</span>
                </div>
                <div>
                    <p className="text-lg font-bold text-gray-900 truncate" title={generalData.summary.top_categories[0]?.name}>
                        {generalData.summary.top_categories[0]?.name || 'N/A'}
                    </p>
                    <p className="text-sm text-gray-500 mt-1">{generalData.summary.top_categories[0]?.count?.toLocaleString() || 0} conversaciones</p>
                </div>
            </div>

            {/* Card 2: Top Subcategoria */}
            <div className="bg-white p-5 rounded-xl shadow-sm border border-gray-100 flex flex-col justify-between">
                <div className="flex items-center justify-between mb-2">
                    <span className="text-xs font-bold text-gray-400 uppercase tracking-wider">Subcategoría más consultada</span>
                </div>
                <div>
                    <p className="text-lg font-bold text-gray-900 truncate" title={topSubcategory.name}>
                        {topSubcategory.name}
                    </p>
                    <p className="text-sm text-gray-500 mt-1">{topSubcategory.count.toLocaleString()} conversaciones</p>
                </div>
            </div>

            {/* Card 3: Top Producto */}
            <div className="bg-white p-5 rounded-xl shadow-sm border border-gray-100 flex flex-col justify-between">
                <div className="flex items-center justify-between mb-2">
                    <span className="text-xs font-bold text-gray-400 uppercase tracking-wider">Producto más consultado</span>
                </div>
                <div>
                    <p className="text-lg font-bold text-gray-900 truncate" title={generalData.summary.top_products[0]?.name}>
                        {generalData.summary.top_products[0]?.name || 'N/A'}
                    </p>
                    <p className="text-sm text-gray-500 mt-1">{generalData.summary.top_products[0]?.count?.toLocaleString() || 0} conversaciones</p>
                </div>
            </div>
        </div>
      </div>

      <hr className="border-gray-200" />

      {/* SECTION B: Category Deep Dive */}
      <div>
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 mb-6">
            <h2 className="text-xl font-bold text-gray-800 flex items-center gap-2">
                <PieChart className="text-blue-500 w-6 h-6"/> Análisis Profundo por Categoría
            </h2>
            {selectedCategory && (
                <button 
                    onClick={() => setSelectedCategory('')}
                    className="flex items-center gap-2 bg-white px-4 py-2 rounded-lg border border-gray-200 shadow-sm text-sm font-medium text-gray-600 hover:bg-gray-50 hover:text-blue-600 transition-colors"
                >
                    Volver al resumen global
                </button>
            )}
        </div>

        {!selectedCategory ? (
            <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-100 overflow-x-auto">
                {/* Tabs */}
                <div className="flex border-b border-gray-200 mb-4">
                    <button
                        className={`py-2 px-4 font-semibold text-sm border-b-2 ${activeTab === 'summary' ? 'border-blue-500 text-blue-600' : 'border-transparent text-gray-500 hover:text-gray-700'}`}
                        onClick={() => setActiveTab('summary')}
                    >
                        Vista Resumen (Categorías)
                    </button>
                    <button
                        className={`py-2 px-4 font-semibold text-sm border-b-2 ${activeTab === 'detailed' ? 'border-blue-500 text-blue-600' : 'border-transparent text-gray-500 hover:text-gray-700'}`}
                        onClick={() => setActiveTab('detailed')}
                    >
                        Vista Detallada
                    </button>
                </div>

                <table className="w-full text-sm text-left text-gray-500">
                    <thead className="text-xs text-gray-700 uppercase bg-gray-50">
                        {activeTab === 'summary' ? (
                            <tr>
                                <th className="px-4 py-3 cursor-pointer select-none hover:bg-gray-100" onClick={() => requestSortA('category')}>
                                    Categoría {sortConfigA?.key === 'category' ? (sortConfigA.direction === 'asc' ? '↑' : '↓') : ''}
                                </th>
                                <th className="px-4 py-3 cursor-pointer select-none hover:bg-gray-100 text-right" onClick={() => requestSortA('unique_conversations')}>
                                    Conversaciones {sortConfigA?.key === 'unique_conversations' ? (sortConfigA.direction === 'asc' ? '↑' : '↓') : ''}
                                </th>
                                <th className="px-4 py-3 cursor-pointer select-none hover:bg-gray-100 text-right" onClick={() => requestSortA('pct_global')}>
                                    % del Total (100%) {sortConfigA?.key === 'pct_global' ? (sortConfigA.direction === 'asc' ? '↑' : '↓') : ''}
                                </th>
                                <th className="px-4 py-3 cursor-pointer select-none hover:bg-gray-100 text-right" onClick={() => requestSortA('pct_referrals')}>
                                    % Deriv. {sortConfigA?.key === 'pct_referrals' ? (sortConfigA.direction === 'asc' ? '↑' : '↓') : ''}
                                </th>
                            </tr>
                        ) : (
                            <tr>
                                <th className="px-4 py-3 cursor-pointer select-none hover:bg-gray-100" onClick={() => requestSortB('category')}>
                                    Categoría {sortConfigB?.key === 'category' ? (sortConfigB.direction === 'asc' ? '↑' : '↓') : ''}
                                </th>
                                <th className="px-4 py-3 cursor-pointer select-none hover:bg-gray-100" onClick={() => requestSortB('intention')}>
                                    Subcategoría {sortConfigB?.key === 'intention' ? (sortConfigB.direction === 'asc' ? '↑' : '↓') : ''}
                                </th>
                                <th className="px-4 py-3 cursor-pointer select-none hover:bg-gray-100" onClick={() => requestSortB('product')}>
                                    Producto {sortConfigB?.key === 'product' ? (sortConfigB.direction === 'asc' ? '↑' : '↓') : ''}
                                </th>
                                <th className="px-4 py-3">Sentimiento Predominante</th>
                                <th className="px-4 py-3 cursor-pointer select-none hover:bg-gray-100 text-right" onClick={() => requestSortB('unique_conversations')}>
                                    Conversaciones {sortConfigB?.key === 'unique_conversations' ? (sortConfigB.direction === 'asc' ? '↑' : '↓') : ''}
                                </th>
                                <th className="px-4 py-3 cursor-pointer select-none hover:bg-gray-100 text-right" onClick={() => requestSortB('pct_human')}>
                                    % Humano {sortConfigB?.key === 'pct_human' ? (sortConfigB.direction === 'asc' ? '↑' : '↓') : ''}
                                </th>
                                <th className="px-4 py-3 cursor-pointer select-none hover:bg-gray-100 text-right" onClick={() => requestSortB('pct_referrals')}>
                                    % Deriv. {sortConfigB?.key === 'pct_referrals' ? (sortConfigB.direction === 'asc' ? '↑' : '↓') : ''}
                                </th>
                                <th className="px-4 py-3 text-right">Acción</th>
                            </tr>
                        )}
                    </thead>
                    <tbody>
                        {activeTab === 'summary' ? (
                            sortedGroupedData.map((row: GroupedCategoryRow, idx: number) => {
                                const globalConversations = generalData?.conversations.total || 1; // avoid div by 0
                                const pctGlobal = Math.round((row.unique_conversations / globalConversations) * 100);
                                const refPct = row.unique_conversations > 0 ? Math.round((row.servilinea_referrals / row.unique_conversations) * 100) : 0;
                                
                                return (
                                    <tr key={idx} className="bg-white border-b hover:bg-gray-50">
                                        <td className="px-4 py-3 font-semibold text-gray-900">{row.category}</td>
                                        <td className="px-4 py-3 text-right font-medium">{row.unique_conversations}</td>
                                        <td className="px-4 py-3 text-right">
                                            <span className="font-bold text-gray-700">{pctGlobal}%</span>
                                        </td>
                                        <td className="px-4 py-3 text-right">
                                            <span className={`text-xs font-bold ${refPct > 20 ? 'text-red-600' : 'text-gray-500'}`}>{refPct}%</span>
                                        </td>
                                    </tr>
                                );
                            })
                        ) : (
                            sortedDetailedData.map((row, idx) => {
                                const totalMsgs = row.human_msgs + row.ai_msgs + row.tool_msgs;
                                const humanPct = totalMsgs > 0 ? Math.round((row.human_msgs / totalMsgs) * 100) : 0;
                                const refPct = row.unique_conversations > 0 ? Math.round((row.servilinea_referrals / row.unique_conversations) * 100) : 0;
                                
                                // Determine dominant sentiment
                                let sentiment = "Neutral";
                                let sentColor = "bg-gray-100 text-gray-600";
                                if (row.positive > row.neutral && row.positive > row.negative) {
                                    sentiment = "Positivo";
                                    sentColor = "bg-green-100 text-green-800";
                                } else if (row.negative > row.neutral && row.negative > row.positive) {
                                    sentiment = "Negativo";
                                    sentColor = "bg-red-100 text-red-800";
                                }

                                return (
                                    <tr key={idx} className="bg-white border-b hover:bg-gray-50">
                                        <td className="px-4 py-3 font-semibold text-gray-900">{row.category}</td>
                                        <td className="px-4 py-3 italic text-gray-600">{row.intention}</td>
                                        <td className="px-4 py-3 text-gray-600">{row.product}</td>
                                        <td className="px-4 py-3">
                                            <span className={`px-2 py-1 rounded text-[10px] font-bold uppercase tracking-wider ${sentColor}`}>
                                                {sentiment}
                                            </span>
                                        </td>
                                        <td className="px-4 py-3 text-right font-medium">{row.unique_conversations}</td>
                                        <td className="px-4 py-3 text-right">
                                            <div className="flex items-center justify-end gap-1">
                                                <span className={`text-xs font-bold ${humanPct > 50 ? 'text-blue-600' : 'text-gray-500'}`}>{humanPct}%</span>
                                            </div>
                                        </td>
                                        <td className="px-4 py-3 text-right">
                                            <span className={`text-xs font-bold ${refPct > 20 ? 'text-red-600' : 'text-gray-500'}`}>{refPct}%</span>
                                        </td>
                                        <td className="px-4 py-3 text-right">
                                            <button 
                                                onClick={() => setSelectedCategory(row.intention)}
                                                className="text-blue-600 hover:text-blue-800 font-medium hover:underline text-xs"
                                            >
                                                Zoom
                                            </button>
                                        </td>
                                    </tr>
                                );
                            })
                        )}
                        {summaryData.length === 0 && (
                            <tr><td colSpan={8} className="text-center py-4 text-gray-500">Cargando resumen de categorías...</td></tr>
                        )}
                    </tbody>
                </table>
            </div>
        ) : loadingCategory ? (
            <div className="h-40 flex justify-center items-center">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
            </div>
        ) : categoryData?.error ? (
            <div className="bg-yellow-50 p-6 rounded-xl border border-yellow-200 text-yellow-800 flex items-center gap-3">
                <AlertTriangle />
                <p>{categoryData.error}</p>
            </div>
        ) : categoryData && (
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                
                {/* Column 1: Contexto & Referrals */}
                <div className="space-y-6">
                    <div className="bg-gradient-to-br from-blue-50 to-indigo-50 p-6 rounded-xl border border-blue-100 shadow-sm">
                        <h3 className="text-lg font-bold text-blue-900 mb-2">Proporción de Interacción</h3>
                        <p className="text-sm text-blue-800 mb-4">
                            De un total de <strong>{categoryData.messages.total.toLocaleString()}</strong> mensajes en esta categoría:
                        </p>
                        <div className="flex items-baseline gap-2">
                            <span className="text-4xl font-extrabold text-blue-700">{categoryData.messages.human_pct}%</span>
                            <span className="text-blue-600 font-medium">son humanos</span>
                        </div>
                        <p className="text-xs text-blue-600 mt-2">({categoryData.messages.human.toLocaleString()} mensajes enviados por clientes)</p>
                    </div>

                    <div className="bg-gradient-to-br from-red-50 to-orange-50 p-6 rounded-xl border border-red-100 shadow-sm">
                        <div className="flex items-center justify-between mb-2">
                            <h3 className="text-lg font-bold text-red-900">Fuga Telefónica</h3>
                            <PhoneCall className="text-red-500 w-5 h-5"/>
                        </div>
                        <p className="text-sm text-red-800 mb-4">
                            Cantidad de hilos que terminaron en derivación a asesor:
                        </p>
                        <span className="text-4xl font-extrabold text-red-700">{categoryData.referrals.total.toLocaleString()}</span>
                    </div>
                </div>

                {/* Column 2: Mensajes más repetidos */}
                <div className="bg-white p-6 rounded-xl border border-gray-200 shadow-sm lg:col-span-1 space-y-6">
                    <div>
                        <h3 className="text-sm font-bold text-gray-800 mb-3 flex items-center gap-2">
                            <span className="bg-blue-100 text-blue-800 w-2 h-2 rounded-full"></span>
                            Top 5 Mensajes Humano
                        </h3>
                        <ul className="space-y-2">
                            {categoryData.frequent_messages.length > 0 ? categoryData.frequent_messages.map((msg, idx) => (
                                <li key={idx} className="flex justify-between items-start gap-4 p-2.5 bg-gray-50 rounded-lg border border-gray-100">
                                    <div className="flex-1">
                                        <div className="text-xs text-gray-700 italic leading-relaxed">"{msg.text}"</div>
                                        {msg.thread_id && (
                                            <div className="text-[10px] text-gray-500 font-mono mt-1 break-all" title={msg.thread_id}>HILO: {msg.thread_id}</div>
                                        )}
                                    </div>
                                    <span className="bg-blue-100 text-blue-800 text-[10px] font-bold px-2 py-0.5 rounded-full shrink-0">
                                        {msg.count}x
                                    </span>
                                </li>
                            )) : (
                                <li className="text-xs text-gray-400 italic">No hay repeticiones notables.</li>
                            )}
                        </ul>
                    </div>

                    <div className="pt-4 border-t border-gray-100">
                        <h3 className="text-sm font-bold text-gray-800 mb-3 flex items-center gap-2">
                            <span className="bg-purple-100 text-purple-800 w-2 h-2 rounded-full"></span>
                            Top 5 Respuestas IA
                        </h3>
                        <ul className="space-y-2">
                            {categoryData.frequent_messages_ai && categoryData.frequent_messages_ai.length > 0 ? categoryData.frequent_messages_ai.map((msg, idx) => (
                                <li key={idx} className="flex justify-between items-start gap-4 p-2.5 bg-purple-50/30 rounded-lg border border-purple-100/50">
                                    <span className="text-xs text-gray-700 italic leading-relaxed">"{msg.text}"</span>
                                    <span className="bg-purple-100 text-purple-800 text-[10px] font-bold px-2 py-0.5 rounded-full">
                                        {msg.count}x
                                    </span>
                                </li>
                            )) : (
                                <li className="text-xs text-gray-400 italic">No hay repeticiones notables de la IA.</li>
                            )}
                        </ul>
                    </div>
                </div>

                {/* Column 3: Distribución interna (Subcats / Productos) */}
                <div className="bg-white p-6 rounded-xl border border-gray-200 shadow-sm lg:col-span-1">
                    <h3 className="text-lg font-bold text-gray-800 mb-4 flex items-center gap-2">
                        <Hash className="w-5 h-5 text-gray-500"/>
                        Micro-Distribución
                    </h3>
                    
                    <div className="mb-6">
                        <h4 className="text-xs font-bold text-gray-400 uppercase tracking-wider mb-3">Top Subcategorías</h4>
                        <ul className="space-y-2">
                            {categoryData.distribution.subcategories.length > 0 ? categoryData.distribution.subcategories.map(s => (
                                <li key={s.name} className="flex items-center justify-between text-sm">
                                    <span className="text-gray-700 truncate mr-2" title={s.name}>{s.name}</span>
                                    <span className="text-gray-500 font-mono text-xs">{s.count}</span>
                                </li>
                            )) : <span className="text-sm text-gray-500">N/A</span>}
                        </ul>
                    </div>

                    <div>
                        <h4 className="text-xs font-bold text-gray-400 uppercase tracking-wider mb-3">Top Productos Involucrados</h4>
                        <ul className="space-y-2">
                            {categoryData.distribution.products.length > 0 ? categoryData.distribution.products.map(p => (
                                <li key={p.name} className="flex items-center justify-between text-sm">
                                    <span className="text-gray-700 truncate mr-2" title={p.name}>{p.name}</span>
                                    <span className="text-gray-500 font-mono text-xs">{p.count}</span>
                                </li>
                            )) : <span className="text-sm text-gray-500">N/A</span>}
                        </ul>
                    </div>
                </div>

            </div>
        )}
      </div>

    </div>
  );
};
