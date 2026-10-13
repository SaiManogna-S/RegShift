import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import {
  Zap,  ChevronDown, ChevronUp,
  Shield, Plus, CheckCircle2, Loader2
} from 'lucide-react'
import { getImpactResults, listDocuments, getRunsForDocument, createTicket, listTickets } from '../api/client'
import type { ImpactResult, AnalysisRun } from '../types'
import toast from 'react-hot-toast'
import clsx from 'clsx'

function ConfidenceBadge({ level }: { level: 'high' | 'medium' | 'low' }) {
  const cfg = {
    high: { label: 'High Confidence', cls: 'confidence-high' },
    medium: { label: 'Medium Confidence', cls: 'confidence-medium' },
    low: { label: 'Low Confidence', cls: 'confidence-low' },
  }[level]
  return (
    <span className={clsx('px-2 py-0.5 rounded-md text-xs font-semibold', cfg.cls)}>
      {cfg.label}
    </span>
  )
}

function CatalogueTypeBadge({ type }: { type: string }) {
  const map: Record<string, string> = {
    product: 'bg-blue-50 text-blue-700',
    rule: 'bg-amber-50 text-amber-700',
    form: 'bg-violet-50 text-violet-700',
  }
  return <span className={clsx('badge', map[type] || 'badge-draft')}>{type}</span>
}

function ImpactCard({ result, existingTicketRefs }: {
  result: ImpactResult
  existingTicketRefs: Set<number>
}) {
  const [expanded, setExpanded] = useState(false)
  const queryClient = useQueryClient()

  const hasTicket = existingTicketRefs.has(result.id)

  const createMutation = useMutation({
    mutationFn: () => createTicket({ impact_result_id: result.id }),
    onSuccess: (ticket) => {
      queryClient.invalidateQueries({ queryKey: ['tickets'] })
      queryClient.invalidateQueries({ queryKey: ['overview-stats'] })
      toast.success(`Ticket ${ticket.ticket_ref} created`)
    },
    onError: (e: any) => {
      toast.error(e?.response?.data?.detail || 'Failed to create ticket')
    },
  })

  const item = result.catalogue_item
  const req = result.requirement

  return (
    <div className={clsx(
      'border rounded-xl overflow-hidden transition-all duration-200',
      result.confidence === 'high' ? 'border-emerald-200' :
      result.confidence === 'medium' ? 'border-amber-200' : 'border-slate-200'
    )}>
      <div
        className="flex items-start gap-4 p-4 cursor-pointer hover:bg-slate-50/50 transition-colors"
        onClick={() => setExpanded(!expanded)}
      >
        {/* Confidence indicator */}
        <div className={clsx(
          'w-1.5 self-stretch rounded-full flex-shrink-0',
          result.confidence === 'high' ? 'bg-emerald-400' :
          result.confidence === 'medium' ? 'bg-amber-400' : 'bg-slate-300'
        )} />

        <div className="flex-1 min-w-0">
          <div className="flex items-start gap-3 flex-wrap">
            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-2 flex-wrap mb-1">
                {item && <CatalogueTypeBadge type={item.item_type} />}
                <ConfidenceBadge level={result.confidence} />
                {result.is_demo && <span className="badge-demo">Demo</span>}
              </div>
              <h3 className="text-sm font-semibold text-slate-900">
                {item?.name || 'Unknown Item'}
              </h3>
              {item?.jurisdiction && (
                <div className="text-xs text-slate-400 mt-0.5">{item.jurisdiction} · {item.line_of_business}</div>
              )}
            </div>
            <div className="flex items-center gap-2 flex-shrink-0">
              {hasTicket ? (
                <span className="flex items-center gap-1 text-xs text-emerald-600 font-medium">
                  <CheckCircle2 size={13} /> Ticket created
                </span>
              ) : (
                <button
                  id={`create-ticket-${result.id}`}
                  className="btn-primary text-xs py-1.5 px-3"
                  onClick={(e) => { e.stopPropagation(); createMutation.mutate() }}
                  disabled={createMutation.isPending}
                >
                  {createMutation.isPending ? (
                    <><Loader2 size={12} className="animate-spin" /> Creating…</>
                  ) : (
                    <><Plus size={12} /> Create Ticket</>
                  )}
                </button>
              )}
              {expanded ? <ChevronUp size={15} className="text-slate-400" /> : <ChevronDown size={15} className="text-slate-400" />}
            </div>
          </div>

          {/* Match reason preview */}
          <p className="text-xs text-slate-500 mt-2 line-clamp-2">{result.match_reason}</p>
        </div>
      </div>

      {expanded && (
        <div className="border-t border-slate-100 px-5 pb-5 pt-4 space-y-4 bg-white">
          {/* Requirement link */}
          {req && (
            <div>
              <div className="text-xs font-semibold text-slate-500 uppercase tracking-wide mb-2">Linked Requirement</div>
              <div className="flex items-start gap-3 p-3 bg-slate-50 rounded-lg border border-slate-200">
                <span className="badge bg-teal-50 text-teal-700 text-xs font-mono">{req.req_id}</span>
                <div className="flex-1 min-w-0">
                  <p className="text-sm text-slate-800 font-medium">{req.summary}</p>
                  {req.effective_date && (
                    <p className="text-xs text-slate-400 mt-1">Effective: {req.effective_date}</p>
                  )}
                </div>
              </div>
            </div>
          )}

          {/* Source passage */}
          {req?.source_passage && (
            <div>
              <div className="text-xs font-semibold text-slate-500 uppercase tracking-wide mb-2">Regulatory Source Text</div>
              <div className="evidence-block">{req.source_passage}</div>
            </div>
          )}

          {/* Match reasoning */}
          <div>
            <div className="text-xs font-semibold text-slate-500 uppercase tracking-wide mb-2">Match Reasoning</div>
            <p className="text-sm text-slate-700">{result.match_reason}</p>
          </div>

          {/* Suggested action */}
          <div>
            <div className="text-xs font-semibold text-slate-500 uppercase tracking-wide mb-2">Suggested Action</div>
            <p className="text-sm text-slate-700">{result.suggested_action}</p>
          </div>

          {/* Catalogue item details */}
          {item && (
            <div className="p-3 bg-slate-50 rounded-lg border border-slate-200">
              <div className="text-xs font-semibold text-slate-500 uppercase tracking-wide mb-2">
                Catalogue Record
                <span className="ml-2 normal-case font-normal text-slate-400">(Synthetic — not a real carrier system)</span>
              </div>
              <div className="text-sm font-semibold text-slate-800 mb-1">{item.name}</div>
              <p className="text-xs text-slate-600">{item.description}</p>
            </div>
          )}
        </div>
      )}
    </div>
  )
}

function RunSelector({ runs, selectedRun, onSelect }: {
  runs: AnalysisRun[]
  selectedRun: AnalysisRun | null
  onSelect: (run: AnalysisRun) => void
}) {
  return (
    <div className="flex flex-wrap gap-2">
      {runs.map(run => (
        <button
          key={run.id}
          onClick={() => onSelect(run)}
          className={clsx(
            'px-3 py-1.5 rounded-lg text-xs font-medium border transition-all',
            selectedRun?.id === run.id
              ? 'bg-teal-500 text-white border-teal-500'
              : 'bg-white text-slate-600 border-slate-200 hover:border-teal-300'
          )}
        >
          Run #{run.id}
          {run.is_demo && ' (Demo)'}
          {' · '}
          {run.status}
        </button>
      ))}
    </div>
  )
}

export default function ImpactAnalysis() {
  const [selectedDocId, setSelectedDocId] = useState<number | null>(null)
  const [selectedRunId, setSelectedRunId] = useState<number | null>(null)

  const { data: documents } = useQuery({ queryKey: ['documents'], queryFn: listDocuments })
  const { data: tickets } = useQuery({ queryKey: ['tickets'], queryFn: listTickets })

  const completedDocs = documents?.filter(d => d.status === 'ready') || []

  const { data: runs } = useQuery({
    queryKey: ['runs', selectedDocId],
    queryFn: () => getRunsForDocument(selectedDocId!),
    enabled: !!selectedDocId,
  })

  const completedRuns = runs?.filter(r => r.status === 'completed') || []
  const activeRun = selectedRunId ? completedRuns.find(r => r.id === selectedRunId) : completedRuns[0]

  const { data: impacts, isLoading } = useQuery({
    queryKey: ['impact', activeRun?.id],
    queryFn: () => getImpactResults(activeRun!.id),
    enabled: !!activeRun,
  })

  // Track which impact results already have tickets
  const ticketedImpactIds = new Set(tickets?.map(t => t.impact_result_id) || [])

  const byConfidence = {
    high: impacts?.filter(i => i.confidence === 'high') || [],
    medium: impacts?.filter(i => i.confidence === 'medium') || [],
    low: impacts?.filter(i => i.confidence === 'low') || [],
  }

  return (
    <div className="space-y-6 animate-fade-in">
      <div>
        <h1 className="text-2xl font-bold text-slate-900">Impact Analysis</h1>
        <p className="text-slate-500 mt-1 text-sm">
          See which products, underwriting rules, and policy forms may be affected by extracted regulatory requirements.
        </p>
      </div>

      {/* Disclaimer */}
      <div className="demo-banner">
        <Shield size={14} />
        <span>
          Insurance catalogue is <strong>synthetic and fictional</strong> — for demonstration only.
          Not integrated with Guidewire, Duck Creek, or any carrier system.
        </span>
      </div>

      {/* Document selector */}
      <div className="card">
        <h2 className="section-heading mb-3">Select Analysis Run</h2>
        {completedDocs.length === 0 ? (
          <div className="text-center py-8">
            <Zap size={32} className="text-slate-200 mx-auto mb-3" />
            <p className="text-slate-400 text-sm">
              No analyzed documents yet. Upload a document and run analysis first, or load the demo scenario.
            </p>
          </div>
        ) : (
          <div className="space-y-4">
            <div>
              <label className="text-xs font-semibold text-slate-500 uppercase tracking-wide mb-2 block">
                Document
              </label>
              <select
                className="input max-w-sm"
                value={selectedDocId ?? ''}
                onChange={(e) => {
                  setSelectedDocId(Number(e.target.value) || null)
                  setSelectedRunId(null)
                }}
              >
                <option value="">Select a document…</option>
                {completedDocs.map(doc => (
                  <option key={doc.id} value={doc.id}>
                    {doc.original_name} {doc.is_demo ? '(Demo)' : ''}
                  </option>
                ))}
              </select>
            </div>

            {completedRuns.length > 1 && (
              <div>
                <label className="text-xs font-semibold text-slate-500 uppercase tracking-wide mb-2 block">
                  Analysis Run
                </label>
                <RunSelector
                  runs={completedRuns}
                  selectedRun={activeRun || null}
                  onSelect={(run) => setSelectedRunId(run.id)}
                />
              </div>
            )}
          </div>
        )}
      </div>

      {/* Results */}
      {activeRun && (
        <div className="space-y-6">
          {isLoading ? (
            <div className="space-y-3">
              {[...Array(4)].map((_, i) => <div key={i} className="skeleton h-20 rounded-xl" />)}
            </div>
          ) : impacts?.length === 0 ? (
            <div className="card text-center py-12">
              <CheckCircle2 size={36} className="text-slate-200 mx-auto mb-3" />
              <p className="text-slate-600 font-medium">No impacts identified</p>
              <p className="text-slate-400 text-sm mt-1">
                No catalogue items matched the extracted requirements. This may mean the regulation does not affect these products.
              </p>
            </div>
          ) : (
            <>
              <div className="flex items-center gap-3">
                <h2 className="section-heading mb-0">
                  {impacts?.length} Potential Impacts Found
                </h2>
                <div className="flex gap-2">
                  {byConfidence.high.length > 0 && <span className="badge confidence-high">{byConfidence.high.length} High</span>}
                  {byConfidence.medium.length > 0 && <span className="badge confidence-medium">{byConfidence.medium.length} Medium</span>}
                  {byConfidence.low.length > 0 && <span className="badge bg-slate-100 text-slate-500">{byConfidence.low.length} Low</span>}
                </div>
              </div>

              {byConfidence.high.length > 0 && (
                <section>
                  <h3 className="text-xs font-bold text-emerald-700 uppercase tracking-widest mb-3">High Confidence Matches</h3>
                  <div className="space-y-3">
                    {byConfidence.high.map(r => (
                      <ImpactCard key={r.id} result={r} existingTicketRefs={ticketedImpactIds} />
                    ))}
                  </div>
                </section>
              )}

              {byConfidence.medium.length > 0 && (
                <section>
                  <h3 className="text-xs font-bold text-amber-600 uppercase tracking-widest mb-3">Medium Confidence Matches</h3>
                  <div className="space-y-3">
                    {byConfidence.medium.map(r => (
                      <ImpactCard key={r.id} result={r} existingTicketRefs={ticketedImpactIds} />
                    ))}
                  </div>
                </section>
              )}

              {byConfidence.low.length > 0 && (
                <section>
                  <h3 className="text-xs font-bold text-slate-500 uppercase tracking-widest mb-3">Low Confidence — Review Recommended</h3>
                  <div className="space-y-3">
                    {byConfidence.low.map(r => (
                      <ImpactCard key={r.id} result={r} existingTicketRefs={ticketedImpactIds} />
                    ))}
                  </div>
                </section>
              )}
            </>
          )}
        </div>
      )}
    </div>
  )
}
