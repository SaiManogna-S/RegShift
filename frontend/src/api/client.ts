import axios from 'axios';
import type {
  Document, AnalysisRun, Requirement, ImpactResult,
  ChangeTicket, AuditEvent, OverviewStats, DemoLoadResult,
  ReviewAction, TicketCreate, TicketUpdate, CatalogueItem
} from '../types';

const BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export const api = axios.create({
  baseURL: BASE_URL,
  timeout: 120000, // 2 min for LLM calls
});

// ---- Documents ----

export const uploadDocument = (file: File, onProgress?: (pct: number) => void) => {
  const form = new FormData();
  form.append('file', file);
  return api.post<Document>('/documents/upload', form, {
    headers: { 'Content-Type': 'multipart/form-data' },
    onUploadProgress: (e) => {
      if (e.total && onProgress) onProgress(Math.round((e.loaded / e.total) * 100));
    },
  }).then(r => r.data);
};

export const listDocuments = () =>
  api.get<Document[]>('/documents/').then(r => r.data);

export const getDocument = (id: number) =>
  api.get<Document>(`/documents/${id}`).then(r => r.data);

export const getDocumentText = (id: number) =>
  api.get<{ document_id: number; text: string }>(`/documents/${id}/text`).then(r => r.data);

// ---- Analysis ----

export const startAnalysis = (documentId: number) =>
  api.post<AnalysisRun>(`/analysis/start/${documentId}`).then(r => r.data);

export const getAnalysisRun = (runId: number) =>
  api.get<AnalysisRun>(`/analysis/${runId}`).then(r => r.data);

export const getRequirements = (runId: number) =>
  api.get<Requirement[]>(`/analysis/${runId}/requirements`).then(r => r.data);

export const getRunsForDocument = (documentId: number) =>
  api.get<AnalysisRun[]>(`/analysis/document/${documentId}/runs`).then(r => r.data);

// ---- Impact ----

export const getImpactResults = (runId: number) =>
  api.get<ImpactResult[]>(`/impact/${runId}`).then(r => r.data);

export const getCatalogue = () =>
  api.get<CatalogueItem[]>('/impact/catalogue/all').then(r => r.data);

// ---- Tickets ----

export const createTicket = (data: TicketCreate) =>
  api.post<ChangeTicket>('/tickets/', data).then(r => r.data);

export const listTickets = () =>
  api.get<ChangeTicket[]>('/tickets/').then(r => r.data);

export const getTicket = (id: number) =>
  api.get<ChangeTicket>(`/tickets/${id}`).then(r => r.data);

export const updateTicket = (id: number, data: TicketUpdate) =>
  api.patch<ChangeTicket>(`/tickets/${id}`, data).then(r => r.data);

export const submitTicketForReview = (id: number) =>
  api.post<ChangeTicket>(`/tickets/${id}/submit`).then(r => r.data);

export const reviewTicket = (id: number, action: ReviewAction) =>
  api.post<ChangeTicket>(`/tickets/${id}/review`, action).then(r => r.data);

// ---- Audit ----

export const getAuditEvents = (limit = 100, offset = 0) =>
  api.get<AuditEvent[]>('/audit/', { params: { limit, offset } }).then(r => r.data);

// ---- Overview ----

export const getOverviewStats = () =>
  api.get<OverviewStats>('/overview/stats').then(r => r.data);

// ---- Demo ----

export const loadDemo = () =>
  api.post<DemoLoadResult>('/demo/load').then(r => r.data);

export const resetDemo = () =>
  api.post('/demo/reset').then(r => r.data);

export const getDemoStatus = () =>
  api.get<{ demo_loaded: boolean; demo_documents: number }>('/demo/status').then(r => r.data);

// ---- Health ----

export const checkHealth = () =>
  api.get('/health').then(r => r.data);
