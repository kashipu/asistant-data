import React, { useEffect, useState, useMemo } from 'react';
import { api } from '../services/api';
import { TrendingUp, ThumbsDown, ThumbsUp, PieChart as PieChartIcon, Activity, ArrowUpDown, ChevronUp, ChevronDown } from 'lucide-react';

interface ReportsPanelProps {
  startDate?: string;
  endDate?: string;
}

type SortConfig<T> = {
  key: keyof T;
  direction: 'asc' | 'desc';
} | null;

export const ReportsPanel: React.FC<ReportsPanelProps> = ({ startDate, endDate }) => {
  const [volumes, setVolumes] = useState<Array<{
    macro_yaml: string;
    categoria_yaml: string;
    product_yaml: string;
    count: number;
    percentage: number;
  }>>([]);
  const [surveyAnalysis, setSurveyAnalysis] = useState<Array<{
    macro: string;
    categoria: string;
    producto: string;
    useful: number;
    not_useful: number;
    total: number;
    utility_rate: number;
  }>>([]);
  const [loading, setLoading] = useState(true);

  // Sorting state
  const [volumeSort, setVolumeSort] = useState<SortConfig<typeof volumes[0]>>({ key: 'count', direction: 'desc' });
  const [surveySort, setSurveySort] = useState<SortConfig<typeof surveyAnalysis[0]>>({ key: 'utility_rate', direction: 'desc' });

  useEffect(() => {
    const fetchData = async () => {
      setLoading(true);
      try {
        const params = { start_date: startDate, end_date: endDate };
        const [vData, sData] = await Promise.all([
          api.getReportVolumes(params),
          api.getReportSurveysLogic(params)
        ]);
        setVolumes(vData);
        setSurveyAnalysis(sData);
      } catch (error) {
        console.error("Error fetching report data:", error);
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, [startDate, endDate]);

  const sortedVolumes = useMemo(() => {
    if (!volumeSort) return volumes;
    return [...volumes].sort((a, b) => {
      const aVal = a[volumeSort.key];
      const bVal = b[volumeSort.key];
      if (aVal < bVal) return volumeSort.direction === 'asc' ? -1 : 1;
      if (aVal > bVal) return volumeSort.direction === 'asc' ? 1 : -1;
      return 0;
    });
  }, [volumes, volumeSort]);

  const sortedSurvey = useMemo(() => {
    if (!surveySort) return surveyAnalysis;
    return [...surveyAnalysis].sort((a, b) => {
      const aVal = a[surveySort.key];
      const bVal = b[surveySort.key];
      if (aVal < bVal) return surveySort.direction === 'asc' ? -1 : 1;
      if (aVal > bVal) return surveySort.direction === 'asc' ? 1 : -1;
      return 0;
    });
  }, [surveyAnalysis, surveySort]);

  const requestVolumeSort = (key: keyof typeof volumes[0]) => {
    let direction: 'asc' | 'desc' = 'desc';
    if (volumeSort?.key === key && volumeSort.direction === 'desc') {
      direction = 'asc';
    }
    setVolumeSort({ key, direction });
  };

  const requestSurveySort = (key: keyof typeof surveyAnalysis[0]) => {
    let direction: 'asc' | 'desc' = 'desc';
    if (surveySort?.key === key && surveySort.direction === 'desc') {
      direction = 'asc';
    }
    setSurveySort({ key, direction });
  };

  const SortIcon = ({ currentSort, columnKey }: { currentSort: SortConfig<any>, columnKey: string }) => {
    if (currentSort?.key !== columnKey) return <ArrowUpDown size={14} className="opacity-40 group-hover:opacity-100 transition-opacity" />;
    return currentSort.direction === 'asc' ? <ChevronUp size={14} className="text-blue-600" /> : <ChevronDown size={14} className="text-blue-600" />;
  };

  if (loading) return (
    <div className="flex flex-col items-center justify-center p-12 text-gray-500">
      <div className="animate-spin rounded-full h-10 w-10 border-b-2 border-blue-600 mb-4"></div>
      Cargando informes de analítica profunda...
    </div>
  );

  return (
    <div className="space-y-8 pb-12 animate-in fade-in duration-500">
      {/* 1. Informe de Volúmenes por Categoría y Producto */}
      <section className="bg-white p-6 rounded-xl border border-gray-200 shadow-sm overflow-hidden">
        <div className="flex justify-between items-center mb-6">
          <div>
            <h3 className="text-xl font-bold text-gray-900 flex items-center gap-2">
              <PieChartIcon className="text-blue-600" />
              Volúmenes de solicitudes (Humanos)
            </h3>
            <p className="text-sm text-gray-500">Distribución de las peticiones de usuarios por categoría y producto (YAML Mapping)</p>
          </div>
          <div className="px-3 py-1 bg-blue-50 text-blue-700 text-xs font-bold rounded-full uppercase tracking-wider">
            Solo Humanos
          </div>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-sm text-left text-gray-500">
            <thead className="text-xs text-gray-400 uppercase bg-gray-50/50">
              <tr>
                <th 
                  className="px-6 py-4 font-bold cursor-pointer hover:bg-gray-100 transition-colors group"
                  onClick={() => requestVolumeSort('categoria_yaml')}
                >
                  <div className="flex items-center gap-2">
                    Macro / Subcategoría <SortIcon currentSort={volumeSort} columnKey="categoria_yaml" />
                  </div>
                </th>
                <th 
                  className="px-6 py-4 font-bold cursor-pointer hover:bg-gray-100 transition-colors group"
                  onClick={() => requestVolumeSort('product_yaml')}
                >
                  <div className="flex items-center gap-2">
                    Producto <SortIcon currentSort={volumeSort} columnKey="product_yaml" />
                  </div>
                </th>
                <th 
                  className="px-6 py-4 text-right font-bold cursor-pointer hover:bg-gray-100 transition-colors group"
                  onClick={() => requestVolumeSort('count')}
                >
                  <div className="flex items-center justify-end gap-2">
                    Volumen <SortIcon currentSort={volumeSort} columnKey="count" />
                  </div>
                </th>
                <th 
                  className="px-6 py-4 text-right font-bold cursor-pointer hover:bg-gray-100 transition-colors group"
                  onClick={() => requestVolumeSort('percentage')}
                >
                  <div className="flex items-center justify-end gap-2">
                    % <SortIcon currentSort={volumeSort} columnKey="percentage" />
                  </div>
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100 border-t border-gray-100">
              {sortedVolumes.length > 0 ? sortedVolumes.map((v, i) => (
                <tr key={i} className="group hover:bg-blue-50/20 transition-colors">
                  <td className="px-6 py-4">
                    <span className="block text-[10px] text-gray-400 font-bold uppercase leading-none mb-1 group-hover:text-blue-500">{v.macro_yaml}</span>
                    <span className="font-bold text-gray-900">{v.categoria_yaml}</span>
                  </td>
                  <td className="px-6 py-4 italic text-gray-400">{v.product_yaml}</td>
                  <td className="px-6 py-4 text-right font-mono font-bold text-gray-700 text-lg">{v.count.toLocaleString()}</td>
                  <td className="px-6 py-4 text-right">
                    <div className="flex items-center justify-end gap-3">
                      <div className="w-24 h-2 bg-gray-100 rounded-full overflow-hidden hidden sm:block">
                        <div className="h-full bg-blue-500 transition-all duration-1000 shadow-[0_0_8px_rgba(37,99,235,0.4)]" style={{ width: `${v.percentage}%` }}></div>
                      </div>
                      <span className="font-bold text-gray-900 min-w-[45px]">{v.percentage}%</span>
                    </div>
                  </td>
                </tr>
              )) : (
                <tr>
                  <td colSpan={4} className="px-6 py-12 text-center text-gray-400 italic">No hay datos para este periodo</td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </section>

      {/* 2. Análisis de Utilidad de Encuesta por Tema */}
      <section className="bg-white p-6 rounded-xl border border-gray-200 shadow-sm overflow-hidden">
        <div className="flex justify-between items-center mb-6">
          <div>
            <h3 className="text-xl font-bold text-gray-900 flex items-center gap-2">
              <TrendingUp className="text-emerald-600" />
              Eficiencia y Utilidad por Categoría
            </h3>
            <p className="text-sm text-gray-500">¿Dónde está fallando o acertando la información del chatbot? (Basado en [survey])</p>
          </div>
           <div className="px-3 py-1 bg-emerald-50 text-emerald-700 text-xs font-bold rounded-full uppercase tracking-wider">
            Feedback Loop
          </div>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-sm text-left text-gray-500">
            <thead className="text-xs text-gray-400 uppercase bg-gray-50/50">
              <tr>
                <th 
                  className="px-6 py-4 font-bold cursor-pointer hover:bg-gray-100 transition-colors group"
                  onClick={() => requestSurveySort('categoria')}
                >
                  <div className="flex items-center gap-2">
                    Categoría <SortIcon currentSort={surveySort} columnKey="categoria" />
                  </div>
                </th>
                <th 
                  className="px-6 py-4 text-center font-bold cursor-pointer hover:bg-gray-100 transition-colors group"
                  onClick={() => requestSurveySort('total')}
                >
                  <div className="flex items-center justify-center gap-2">
                    Total Encuestas <SortIcon currentSort={surveySort} columnKey="total" />
                  </div>
                </th>
                <th className="px-6 py-4 text-center font-bold">Útil / No Útil</th>
                <th 
                  className="px-6 py-4 text-right font-bold cursor-pointer hover:bg-gray-100 transition-colors group"
                  onClick={() => requestSurveySort('utility_rate')}
                >
                  <div className="flex items-center justify-end gap-2">
                    Tasa Utilidad <SortIcon currentSort={surveySort} columnKey="utility_rate" />
                  </div>
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100 border-t border-gray-100">
              {sortedSurvey.length > 0 ? sortedSurvey.map((s, i) => (
                <tr key={i} className="hover:bg-emerald-50/10 transition-colors">
                  <td className="px-6 py-4 font-bold text-gray-900">{s.categoria}</td>
                  <td className="px-6 py-4 text-center font-mono font-bold text-gray-700">{s.total}</td>
                  <td className="px-6 py-4 text-center">
                     <div className="flex items-center justify-center gap-4 text-sm font-bold font-mono">
                        <div className="flex flex-col items-center">
                           <span className="text-emerald-600">{s.useful}</span>
                           <span className="text-[10px] text-emerald-400 uppercase tracking-tighter">Útil</span>
                        </div>
                        <span className="text-gray-300 text-xl font-light">/</span>
                        <div className="flex flex-col items-center">
                           <span className="text-red-500">{s.not_useful}</span>
                           <span className="text-[10px] text-red-300 uppercase tracking-tighter">No útil</span>
                        </div>
                     </div>
                  </td>
                  <td className="px-6 py-4 text-right">
                    <span className={`inline-flex items-center justify-center w-16 h-16 rounded-full text-base font-extrabold shadow-sm border-2 ${
                      s.utility_rate > 70 ? 'bg-emerald-50 text-emerald-700 border-emerald-200 shadow-emerald-100' : 
                      s.utility_rate > 40 ? 'bg-amber-50 text-amber-700 border-amber-200 shadow-amber-100' : 
                      'bg-rose-50 text-rose-700 border-rose-200 shadow-rose-100'
                    }`}>
                      {s.utility_rate}%
                    </span>
                  </td>
                </tr>
              )) : (
                <tr>
                  <td colSpan={4} className="px-6 py-12 text-center text-gray-400 italic">No hay datos de encuestas para este periodo</td>
                </tr>
              )}
            </tbody>
          </table>
        </div>

        <div className="mt-8 grid grid-cols-1 md:grid-cols-3 gap-6">
           {surveyAnalysis.filter(s => s.utility_rate < 40 && s.total > 5).sort((a,b) => a.utility_rate - b.utility_rate).slice(0,3).map((s, i) => (
             <div key={i} className="bg-rose-50/50 border border-rose-100 p-5 rounded-2xl shadow-sm hover:shadow-md transition-shadow">
                <div className="flex items-center gap-2 text-rose-700 mb-3 font-bold text-xs uppercase tracking-wider">
                   <div className="p-1.5 bg-rose-100 rounded-lg"><ThumbsDown size={14} /></div> Foco de Mejora
                </div>
                <div className="text-xl font-extrabold text-gray-900 leading-tight mb-2">{s.categoria}</div>
                <div className="text-sm text-gray-600 leading-relaxed font-medium">
                   Solo el <span className="text-rose-600 font-bold text-base">{s.utility_rate}%</span> de los usuarios encuentran útil la información. <span className="block mt-1 text-xs text-rose-400">({s.not_useful} críticas negativas)</span>
                </div>
             </div>
           ))}
           {surveyAnalysis.filter(s => s.utility_rate > 75 && s.total > 5).sort((a,b) => b.utility_rate - a.utility_rate).slice(0,3).map((s, i) => (
             <div key={i} className="bg-emerald-50/50 border border-emerald-100 p-5 rounded-2xl shadow-sm hover:shadow-md transition-shadow">
                <div className="flex items-center gap-2 text-emerald-700 mb-3 font-bold text-xs uppercase tracking-wider">
                   <div className="p-1.5 bg-emerald-100 rounded-lg"><ThumbsUp size={14} /></div> Caso de Éxito
                </div>
                <div className="text-xl font-extrabold text-gray-900 leading-tight mb-2">{s.categoria}</div>
                <div className="text-sm text-gray-600 leading-relaxed font-medium">
                   Excelente desempeño (<span className="text-emerald-700 font-bold text-base">{s.utility_rate}%</span>). La respuesta satisface a la inmensa mayoría.
                </div>
             </div>
           ))}
           {surveyAnalysis.length === 0 && (
              <div className="col-span-3 text-center p-12 bg-gray-50 rounded-2xl border-2 border-dashed border-gray-200">
                  <Activity className="mx-auto text-gray-300 mb-3 w-10 h-10" />
                  <p className="text-gray-500 font-bold text-lg">No hay suficientes datos de encuestas</p>
                  <p className="text-gray-400 text-sm">Prueba ampliando el rango de fechas para generar recomendaciones.</p>
              </div>
           )}
        </div>
      </section>
    </div>
  );
};
