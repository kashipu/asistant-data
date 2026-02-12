
import axios from 'axios';

const API_URL = 'http://localhost:8000/api';

export const api = {
    getKpis: () => axios.get(`${API_URL}/kpis`).then(res => res.data),
    getFailures: (params: { page: number, limit: number, start_date?: string, end_date?: string }) => axios.get(`${API_URL}/failures`, { params }).then(res => res.data),
    getReferrals: (params: { page: number, limit: number, start_date?: string, end_date?: string }) => axios.get(`${API_URL}/referrals`, { params }).then(res => res.data),
    getMessages: (params: { page: number, limit: number, search?: string, intencion?: string, sentiment?: string, product?: string, sender_type?: string, thread_id?: string, start_date?: string, end_date?: string, exclude_empty?: boolean, sort_by?: string }) => axios.get(`${API_URL}/messages`, { params }).then(res => res.data),
    getOptions: () => axios.get(`${API_URL}/options`).then(res => res.data),
    getCategoricalAnalysis: () => axios.get(`${API_URL}/analysis/categorical`).then(res => res.data),
    getTemporalAnalysis: () => axios.get(`${API_URL}/analysis/temporal`).then(res => res.data),
    getWordCloud: (intencion?: string) => axios.get(`${API_URL}/analysis/wordcloud`, { params: { intencion } }).then(res => res.data),
    getConversationAnalysis: (threadId?: string) => axios.get(`${API_URL}/analysis/conversations`, { params: { thread_id: threadId } }).then(res => res.data),
    getSummary: (start_date?: string, end_date?: string) => axios.get(`${API_URL}/summary`, { params: { start_date, end_date } }).then(res => res.data),
  getUncategorized: (page = 1, limit = 20, start_date?: string, end_date?: string) => axios.get(`${API_URL}/analysis/uncategorized`, { params: { page, limit, start_date, end_date } }).then(res => res.data),
  getSurveys: (start_date?: string, end_date?: string) => axios.get(`${API_URL}/analysis/surveys`, { params: { start_date, end_date } }).then(res => res.data),
  getAdvisors: (start_date?: string, end_date?: string) => axios.get(`${API_URL}/advisors`, { params: { start_date, end_date } }).then(res => res.data),
  getInsights: () => axios.get(`${API_URL}/insights`).then(res => res.data),
};
