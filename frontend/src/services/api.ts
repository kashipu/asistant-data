
import axios from 'axios';

const API_URL = 'http://127.0.0.1:8000/api';

export const api = {
    getKPIs: (): Promise<{
    total_conversations: number;
    total_messages: number;
    avg_messages_per_thread: number;
    avg_human_messages_per_thread: number;
    abandonment_rate: number;
  }> => axios.get(`${API_URL}/kpis`).then(res => res.data),
    getFailures: (params: { page: number, limit: number, start_date?: string, end_date?: string }) => axios.get(`${API_URL}/failures`, { params }).then(res => res.data),
    getReferrals: (params: { page: number, limit: number, start_date?: string, end_date?: string }) => axios.get(`${API_URL}/referrals`, { params }).then(res => res.data),
    getMessages: (params: { page: number, limit: number, search?: string, intencion?: string, macro_categoria?: string, sentiment?: string, product?: string, sender_type?: string, thread_id?: string, start_date?: string, end_date?: string, exclude_empty?: boolean, sort_by?: string, survey_result?: string }) => axios.get(`${API_URL}/messages`, { params }).then(res => res.data),
    getOptions: () => axios.get(`${API_URL}/options`).then(res => res.data),
    getCategoricalAnalysis: (start_date?: string, end_date?: string) => axios.get(`${API_URL}/analysis/categorical`, { params: { start_date, end_date } }).then(res => res.data),
    getTemporalAnalysis: (params?: { start_date?: string; end_date?: string }): Promise<{
    daily_volume: Record<string, number>;
    hourly_volume: Record<string, number>;
    day_of_week_volume: Record<string, number>;
    heatmap: Array<{ day: string; hour: number; count: number }>;
  }> => axios.get(`${API_URL}/analysis/temporal`, { params }).then(res => res.data),
    getWordCloud: (intencion?: string) => axios.get(`${API_URL}/analysis/wordcloud`, { params: { intencion } }).then(res => res.data),
    getConversationAnalysis: (threadId?: string) => axios.get(`${API_URL}/analysis/conversations`, { params: { thread_id: threadId } }).then(res => res.data),
    getSummary: (start_date?: string, end_date?: string) => axios.get(`${API_URL}/summary`, { params: { start_date, end_date } }).then(res => res.data),
  getUncategorized: (page = 1, limit = 20, start_date?: string, end_date?: string) => axios.get(`${API_URL}/analysis/uncategorized`, { params: { page, limit, start_date, end_date } }).then(res => res.data),
  getSurveys: (start_date?: string, end_date?: string) => axios.get(`${API_URL}/analysis/surveys`, { params: { start_date, end_date } }).then(res => res.data),
  getAdvisors: (start_date?: string, end_date?: string) => axios.get(`${API_URL}/advisors`, { params: { start_date, end_date } }).then(res => res.data),
  getInsights: () => axios.get(`${API_URL}/insights`).then(res => res.data),
  getFeedbacks: (page = 1, limit = 20) => axios.get(`${API_URL}/feedbacks`, { params: { page, limit } }).then(res => res.data),
  getFeedbackOptions: () => axios.get(`${API_URL}/feedbacks/options`).then(res => res.data),
  categorizeFeedback: (data: { message_id: string, new_category: string, new_sentiment?: string, new_product?: string, original_text: string }) => axios.post(`${API_URL}/feedbacks/categorize`, data).then(res => res.data),
  runEtl: () => axios.post(`${API_URL}/etl/run`).then(res => res.data),
  getEtlStatus: () => axios.get(`${API_URL}/etl/status`).then(res => res.data),
  getFaqs: (top_n = 5) => axios.get(`${API_URL}/faqs`, { params: { top_n } }).then(res => res.data),
  getQualitativeInsights: () => axios.get(`${API_URL}/insights/qualitative`).then(res => res.data),
  getCategoryInsights: (categoria: string) => axios.get(`${API_URL}/insights/category`, { params: { categoria } }).then(res => res.data),
  getReportVolumes: (params?: { start_date?: string; end_date?: string }) => axios.get(`${API_URL}/reports/volumes`, { params }).then(res => res.data),
  getReportSurveysLogic: (params?: { start_date?: string; end_date?: string }) => axios.get(`${API_URL}/reports/surveys/logic`, { params }).then(res => res.data),
  getGaps: (params?: { start_date?: string; end_date?: string }) => axios.get(`${API_URL}/analysis/gaps`, { params }).then(res => res.data),
  getFunnel: (params?: { start_date?: string; end_date?: string }) => axios.get(`${API_URL}/dashboard/funnel`, { params }).then(res => res.data),
  getDataPeriod: () => axios.get(`${API_URL}/info/data-period`).then(res => res.data),
  getKpisDetailed: (params?: { start_date?: string; end_date?: string }) =>
    axios.get(`${API_URL}/reports/kpis-detailed`, { params }).then(r => r.data),
  getCategoriesDetailed: (params?: { start_date?: string; end_date?: string }) =>
    axios.get(`${API_URL}/reports/categories-detailed`, { params }).then(r => r.data),
  getProductsDetailed: (params?: { start_date?: string; end_date?: string }) =>
    axios.get(`${API_URL}/reports/products-detailed`, { params }).then(r => r.data),
  getCategoryThreads: (params: {
    macro?: string;
    subcategory?: string;
    product?: string;
    cross_category?: string;
    page?: number;
    limit?: number;
    start_date?: string;
    end_date?: string;
    exclude_greetings?: boolean;
    product_macro?: string;
    failures_only?: boolean;
  }) => axios.get(`${API_URL}/reports/category-threads`, { params }).then(r => r.data),
  getFailuresDetailed: (params?: { start_date?: string; end_date?: string }) =>
    axios.get(`${API_URL}/reports/failures-detailed`, { params }).then(r => r.data),
  downloadMarkdownReport: async (opts?: {
    startDate?: string;
    endDate?: string;
    full?: boolean;
    reportType?: 'executive' | 'deep';
  }) => {
    const params = new URLSearchParams();
    if (opts?.startDate) params.set('start_date', opts.startDate);
    if (opts?.endDate) params.set('end_date', opts.endDate);
    if (opts?.full) params.set('full', 'true');
    if (opts?.reportType) params.set('report_type', opts.reportType);
    const qs = params.toString();
    const url_api = `${API_URL}/reports/export/markdown${qs ? `?${qs}` : ''}`;
    const response = await axios.get(url_api, { responseType: 'blob' });
    const prefix = opts?.reportType === 'deep' ? 'informe_profundo' : 'informe_ejecutivo';
    const url = URL.createObjectURL(new Blob([response.data], { type: 'text/markdown' }));
    const a = document.createElement('a');
    a.href = url;
    a.download = `${prefix}_${new Date().toISOString().slice(0, 10)}.md`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  },
};
