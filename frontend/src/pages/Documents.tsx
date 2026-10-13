import { useState, useRef } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import {
  Upload, FileText, Zap, AlertCircle,
  ChevronDown, ChevronUp, RefreshCw, Loader2
} from 'lucide-react'
import { listDocuments, uploadDocument, startAnalysis, getRunsForDocument, getRequirements } from '../api/client'
import type { Document, Requirement } from '../types'
import { formatDistanceToNow } from 'date-fns'
import toast from 'react-hot-toast'
import clsx from 'clsx'

function StatusBadge({ status }: { status: string }) {
  const map: Record<string, string> = {
    ready: 'badge-ready',
    error: 'badge-error',
    processing: 'badge-processing',
    uploaded: 'badge-processing',
  }
  return <span className={map[status] || 'badge-draft'}>{status}</span>
}

function RunStatusBadge({ status }: { status: string }) {
  const map: Record<string, string> = {
    completed: 'badge-ready',
    failed: 'badge-error',
    running: 'badge-processing',
    pending: 'badge-draft',
  }
  return <span className={map[status] || 'badge-draft'}>{status}</span>
}

function formatBytes(bytes: number) {
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
}

function RequirementCard({ req }: { req: Requirement }) {
  const [expanded, setExpanded] = useState(false)
  return (
    <div className="border border-slate-200 rounded-lg overflow-hidden">
      <button
        className="w-full flex items-start gap-3 p-4 text-left hover:bg-slate-50 transition-colors"
        onClick={() => setExpanded(!expanded)}
      >
        <div className="flex-shrink-0 mt-0.5">
          <div className={clsx(
            'px-1.5 py-0.5 rounded text-xs font-mono font-bold',
            req.is_demo ? 'bg-violet-100 text-violet-700' : 'bg-teal-100 text-teal-700'
          )}>
            {req.req_id}
          </div>
        </div>
        <div className="flex-1 min-w-0">
          <p className="text-sm font-medium text-slate-800 leading-snug">{req.summary}</p>
          <div className="flex flex-wrap gap-2 mt-2">
            {req.jurisdiction && <span className="badge bg-blue-50 text-blue-600">{req.jurisdiction}</span>}
            {req.line_of_business && <span className="badge bg-slate-100 text-slate-600">{req.line_of_business}</span>}
            {req.effective_date && <span className="badge bg-amber-50 text-amber-700">Effective: {req.effective_date}</span>}
            {req.change_category && (
              <span className="badge bg-slate-100 text-slate-500">
                {req.change_category.replace(/_/g, ' ')}
              </span>
            )}
          </div>
        </div>
        {expanded ? <ChevronUp size={16} className="text-slate-400 flex-shrink-0 mt-0.5" /> : <ChevronDown size={16} className="text-slate-400 flex-shrink-0 mt-0.5" />}
      </button>

      {expanded && (
        <div className="px-4 pb-4 space-y-3 border-t border-slate-100 pt-3">
          {req.source_passage && (
            <div>
              <div className="text-xs font-semibold text-slate-500 uppercase tracking-wide mb-1">Source Passage</div>
              <div className="evidence-block">{req.source_passage}</div>
            </div>
          )}
          {req.required_action && (
            <div>
              <div className="text-xs font-semibold text-slate-500 uppercase tracking-wide mb-1">Required Action</div>
              <p className="text-sm text-slate-700">{req.required_action}</p>
            </div>
          )}
          {req.ambiguities && (
            <div className="flex gap-2 p-3 bg-amber-50 border border-amber-200 rounded-lg">
              <AlertCircle size={14} className="text-amber-500 flex-shrink-0 mt-0.5" />
              <div>
                <div className="text-xs font-semibold text-amber-700 mb-0.5">Ambiguities / Unresolved Questions</div>
                <p className="text-xs text-amber-700">{req.ambiguities}</p>
              </div>
            </div>
          )}
          {req.page_ref && (
            <p className="text-xs text-slate-400">Reference: {req.page_ref}</p>
          )}
        </div>
      )}
    </div>
  )
}

function DocumentRow({ doc, onAnalyze }: { doc: Document; onAnalyze: (id: number) => void }) {
  const [expanded, setExpanded] = useState(false)
  const { data: runs } = useQuery({
    queryKey: ['runs', doc.id],
    queryFn: () => getRunsForDocument(doc.id),
    enabled: expanded,
  })
  const latestRun = runs?.[0]

  const { data: requirements } = useQuery({
    queryKey: ['requirements', latestRun?.id],
    queryFn: () => getRequirements(latestRun!.id),
    enabled: !!latestRun && latestRun.status === 'completed',
  })

  const [analyzingId, setAnalyzingId] = useState<number | null>(null)

  const handleAnalyze = async (docId: number) => {
    setAnalyzingId(docId)
    try {
      await onAnalyze(docId)
    } finally {
      setAnalyzingId(null)
    }
  }

  return (
    <div className="border border-slate-200 rounded-xl overflow-hidden">
      <div
        className="flex items-center gap-4 px-5 py-4 hover:bg-slate-50 cursor-pointer transition-colors"
        onClick={() => setExpanded(!expanded)}
      >
        <FileText size={18} className="text-slate-400 flex-shrink-0" />
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 flex-wrap">
            <span className="text-sm font-semibold text-slate-800 truncate">{doc.original_name}</span>
            {doc.is_demo && <span className="badge-demo">Demo</span>}
          </div>
          <div className="text-xs text-slate-400 mt-0.5">
            {formatBytes(doc.file_size)} · Uploaded {formatDistanceToNow(new Date(doc.upload_timestamp), { addSuffix: true })}
          </div>
        </div>
        <div className="flex items-center gap-3 flex-shrink-0">
          <StatusBadge status={doc.status} />
          {doc.status === 'ready' && (
            <button
              id={`analyze-btn-${doc.id}`}
              className="btn-primary text-xs py-1.5 px-3"
              onClick={(e) => { e.stopPropagation(); handleAnalyze(doc.id) }}
              disabled={analyzingId === doc.id}
            >
              {analyzingId === doc.id ? (
                <><Loader2 size={13} className="animate-spin" /> Analyzing…</>
              ) : (
                <><Zap size={13} /> Analyze</>
              )}
            </button>
          )}
          {expanded ? <ChevronUp size={16} className="text-slate-400" /> : <ChevronDown size={16} className="text-slate-400" />}
        </div>
      </div>

      {expanded && (
        <div className="border-t border-slate-100 px-5 py-4 space-y-4 bg-slate-50/50">
          {doc.extraction_error && (
            <div className="flex gap-2 p-3 bg-red-50 border border-red-200 rounded-lg">
              <AlertCircle size={14} className="text-red-500 flex-shrink-0 mt-0.5" />
              <p className="text-sm text-red-700">{doc.extraction_error}</p>
            </div>
          )}

          {/* Analysis runs */}
          {runs && runs.length > 0 && (
            <div>
              <div className="text-xs font-semibold text-slate-500 uppercase tracking-wide mb-2">Analysis Runs</div>
              <div className="space-y-2">
                {runs.map(run => (
                  <div key={run.id} className="flex items-center gap-3 p-3 bg-white rounded-lg border border-slate-200 text-sm">
                    <RunStatusBadge status={run.status} />
                    <span className="text-slate-600 flex-1">
                      Run #{run.id}
                      {run.llm_used ? ' · AI extraction' : ' · Demo mode'}
                      {run.is_demo && ' · Demo'}
                    </span>
                    {run.completed_at && (
                      <span className="text-xs text-slate-400">
                        {formatDistanceToNow(new Date(run.completed_at), { addSuffix: true })}
                      </span>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Requirements */}
          {requirements && requirements.length > 0 && (
            <div>
              <div className="text-xs font-semibold text-slate-500 uppercase tracking-wide mb-2">
                Extracted Requirements ({requirements.length})
              </div>
              {!requirements[0].is_demo && latestRun && !latestRun.llm_used && (
                <div className="demo-banner mb-3">
                  <Zap size={14} />
                  Demo mode — no AI API key configured. Showing illustrative requirements only, not your document.
                </div>
              )}
              <div className="space-y-2">
                {requirements.map(req => (
                  <RequirementCard key={req.id} req={req} />
                ))}
              </div>
            </div>
          )}

          {runs && runs.length === 0 && (
            <p className="text-sm text-slate-400">No analysis runs yet. Click Analyze to extract requirements.</p>
          )}
        </div>
      )}
    </div>
  )
}

export default function Documents() {
  const queryClient = useQueryClient()
  const fileInputRef = useRef<HTMLInputElement>(null)
  const [dragOver, setDragOver] = useState(false)
  const [uploadProgress, setUploadProgress] = useState<number | null>(null)

  const { data: documents, isLoading } = useQuery({
    queryKey: ['documents'],
    queryFn: listDocuments,
  })

  const uploadMutation = useMutation({
    mutationFn: (file: File) => uploadDocument(file, setUploadProgress),
    onSuccess: (doc) => {
      queryClient.invalidateQueries({ queryKey: ['documents'] })
      queryClient.invalidateQueries({ queryKey: ['overview-stats'] })
      toast.success(`"${doc.original_name}" uploaded successfully`)
      setUploadProgress(null)
    },
    onError: (e: any) => {
      toast.error(e?.response?.data?.detail || 'Upload failed')
      setUploadProgress(null)
    },
  })

  const handleFile = (file: File) => {
    const allowed = ['application/pdf', 'text/plain']
    const ext = file.name.toLowerCase()
    if (!allowed.includes(file.type) && !ext.endsWith('.pdf') && !ext.endsWith('.txt')) {
      toast.error('Only PDF and TXT files are supported.')
      return
    }
    if (file.size > 20 * 1024 * 1024) {
      toast.error('File must be under 20 MB.')
      return
    }
    uploadMutation.mutate(file)
  }

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault()
    setDragOver(false)
    const file = e.dataTransfer.files[0]
    if (file) handleFile(file)
  }

  const handleAnalyze = async (docId: number) => {
    try {
      const run = await startAnalysis(docId)
      queryClient.invalidateQueries({ queryKey: ['runs', docId] })
      queryClient.invalidateQueries({ queryKey: ['requirements', run.id] })
      queryClient.invalidateQueries({ queryKey: ['overview-stats'] })
      toast.success('Analysis complete')
    } catch (e: any) {
      toast.error(e?.response?.data?.detail || 'Analysis failed')
    }
  }

  return (
    <div className="space-y-6 animate-fade-in">
      <div>
        <h1 className="text-2xl font-bold text-slate-900">Regulatory Documents</h1>
        <p className="text-slate-500 mt-1 text-sm">Upload regulatory bulletins for requirement extraction and impact analysis.</p>
      </div>

      {/* Upload zone */}
      <div
        id="upload-zone"
        className={clsx(
          'border-2 border-dashed rounded-xl p-10 text-center cursor-pointer transition-all duration-200',
          dragOver ? 'border-teal-400 bg-teal-50' : 'border-slate-200 hover:border-teal-300 hover:bg-slate-50',
          uploadMutation.isPending && 'opacity-70 cursor-not-allowed'
        )}
        onDragOver={(e) => { e.preventDefault(); setDragOver(true) }}
        onDragLeave={() => setDragOver(false)}
        onDrop={handleDrop}
        onClick={() => !uploadMutation.isPending && fileInputRef.current?.click()}
      >
        <input
          ref={fileInputRef}
          type="file"
          accept=".pdf,.txt"
          className="hidden"
          id="file-input"
          onChange={(e) => { const f = e.target.files?.[0]; if (f) handleFile(f) }}
        />
        {uploadMutation.isPending ? (
          <div className="space-y-3">
            <Loader2 size={32} className="text-teal-500 animate-spin mx-auto" />
            <p className="text-sm text-slate-600 font-medium">
              Uploading and extracting text…
              {uploadProgress !== null && ` ${uploadProgress}%`}
            </p>
            {uploadProgress !== null && (
              <div className="w-48 mx-auto bg-slate-200 rounded-full h-1.5">
                <div
                  className="bg-teal-500 h-1.5 rounded-full transition-all duration-300"
                  style={{ width: `${uploadProgress}%` }}
                />
              </div>
            )}
          </div>
        ) : (
          <div className="space-y-3">
            <Upload size={32} className="text-slate-300 mx-auto" />
            <div>
              <p className="text-sm font-semibold text-slate-700">
                Drop a file here or <span className="text-teal-600">browse</span>
              </p>
              <p className="text-xs text-slate-400 mt-1">PDF or TXT · Max 20 MB</p>
            </div>
          </div>
        )}
      </div>

      {/* Document list */}
      <div>
        <div className="flex items-center justify-between mb-3">
          <h2 className="section-heading mb-0">
            Documents {documents && `(${documents.length})`}
          </h2>
          <button
            className="btn-ghost"
            onClick={() => queryClient.invalidateQueries({ queryKey: ['documents'] })}
          >
            <RefreshCw size={14} /> Refresh
          </button>
        </div>

        {isLoading ? (
          <div className="space-y-3">
            {[...Array(3)].map((_, i) => <div key={i} className="skeleton h-16 rounded-xl" />)}
          </div>
        ) : documents?.length === 0 ? (
          <div className="card text-center py-12">
            <FileText size={36} className="text-slate-200 mx-auto mb-3" />
            <p className="text-slate-400 text-sm">No documents yet. Upload one above or load the demo scenario.</p>
          </div>
        ) : (
          <div className="space-y-3">
            {documents?.map(doc => (
              <DocumentRow key={doc.id} doc={doc} onAnalyze={handleAnalyze} />
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
