// All TypeScript types for RegShift frontend

export interface Document {
  id: number;
  filename: string;
  original_name: string;
  file_type: string;
  file_size: number;
  status: 'uploaded' | 'processing' | 'ready' | 'error';
  extraction_error?: string;
  upload_timestamp: string;
  is_demo: boolean;
  has_text: boolean;
}

export interface AnalysisRun {
  id: number;
  document_id: number;
  status: 'pending' | 'running' | 'completed' | 'failed';
  started_at?: string;
  completed_at?: string;
  error_message?: string;
  is_demo: boolean;
  llm_used: boolean;
}

export interface Requirement {
  id: number;
  analysis_run_id: number;
  req_id: string;
  summary: string;
  source_passage?: string;
  page_ref?: string;
  jurisdiction?: string;
  line_of_business?: string;
  effective_date?: string;
  change_category?: string;
  required_action?: string;
  ambiguities?: string;
  is_demo: boolean;
}

export interface CatalogueItem {
  id: number;
  item_type: 'product' | 'rule' | 'form';
  name: string;
  jurisdiction?: string;
  line_of_business?: string;
  description: string;
  keywords?: string;
  is_demo: boolean;
}

export interface ImpactResult {
  id: number;
  analysis_run_id: number;
  requirement_id: number;
  catalogue_item_id: number;
  match_reason: string;
  confidence: 'high' | 'medium' | 'low';
  suggested_action: string;
  is_demo: boolean;
  requirement?: Requirement;
  catalogue_item?: CatalogueItem;
}

export interface ChangeTicket {
  id: number;
  ticket_ref: string;
  title: string;
  requirement_id: number;
  impact_result_id: number;
  proposed_action: string;
  evidence: string;
  priority: 'critical' | 'high' | 'medium' | 'low';
  priority_rationale: string;
  effective_date?: string;
  assumptions?: string;
  status: 'draft' | 'pending_review' | 'approved' | 'rejected' | 'changes_requested';
  reviewer_comment?: string;
  created_at: string;
  updated_at: string;
  is_demo: boolean;
  requirement?: Requirement;
  impact_result?: ImpactResult;
}

export interface AuditEvent {
  id: number;
  event_type: string;
  record_id?: number;
  record_type?: string;
  details?: string;
  timestamp: string;
  is_demo_related: boolean;
}

export interface OverviewStats {
  total_documents: number;
  completed_analyses: number;
  pending_reviews: number;
  open_tickets: number;
  recent_events: AuditEvent[];
}

export interface DemoLoadResult {
  status: string;
  message: string;
  document_id: number;
  analysis_run_id: number;
  requirements_count: number;
  impact_results_count: number;
  catalogue_items_loaded: number;
}

export interface ReviewAction {
  action: 'approve' | 'reject' | 'request_changes';
  comment?: string;
}

export interface TicketCreate {
  impact_result_id: number;
  title?: string;
  proposed_action?: string;
  priority?: string;
  assumptions?: string;
}

export interface TicketUpdate {
  title?: string;
  proposed_action?: string;
  priority?: string;
  assumptions?: string;
}
