import { useQuery } from '@tanstack/react-query'
import { useNavigate } from 'react-router-dom'
import { FileText, Zap, Clock, CheckCircle, TrendingUp, AlertCircle, ArrowRight, Sparkles } from 'lucide-react'
import { getOverviewStats } from '../api/client'
import { formatDistanceToNow } from 'date-fns'
import clsx from 'clsx'

const EVENT_LABELS: Record<string, string> = {
  document_uploaded: 'Document Uploaded',
  analysis_started: 'Analysis Started',
  analysis_completed: 'Analysis Completed',
  analysis_failed: 'Analysis Failed',
  ticket_created: 'Ticket Created',
  ticket_updated: 'Ticket Updated',
  ticket_submitted_for_review: 'Submitted for Review',
  ticket_approved: 'Ticket Approved',
  ticket_rejected: 'Ticket Rejected',
  ticket_changes_requested: 'Changes Requested',
  demo_scenario_loaded: 'Demo Scenario Loaded',
  demo_scenario_reset: 'Demo Reset',
}

const EVENT_COLORS: Record<string, string> = {
  document_uploaded: 'bg-blue-500',
  analysis_completed: 'bg-teal-500',
  analysis_failed: 'bg-red-500',
  ticket_approved: 'bg-emerald-500',
  ticket_rejected: 'bg-red-400',
  demo_scenario_loaded: 'bg-violet-500',
  default: 'bg-slate-400',
}

function StatCard({ label, value, icon: Icon, color, loading }: {
  label: string; value: number; icon: any; color: string; loading: boolean
}) {
  return (
    <div className="stat-card">
      <div className="flex items-center justify-between">
        <span className="text-xs font-semibold text-slate-500 uppercase tracking-wide">{label}</span>
        <div className={clsx('w-8 h-8 rounded-lg flex items-center justify-center', color)}>
          <Icon size={15} className="text-white" />
        </div>
      </div>
      {loading ? (
        <div className="skeleton h-8 w-20 mt-1" />
      ) : (
        <span className="text-3xl font-bold text-slate-900">{value}</span>
      )}
    </div>
  )
}

export default function Overview() {
  const navigate = useNavigate()
  const { data: stats, isLoading } = useQuery({
    queryKey: ['overview-stats'],
    queryFn: getOverviewStats,
    refetchInterval: 30000,
  })

  const isEmpty = !isLoading && stats &&
    stats.total_documents === 0 &&
    stats.completed_analyses === 0 &&
    stats.open_tickets === 0

  return (
    <div className="space-y-8 animate-fade-in">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-slate-900">Overview</h1>
        <p className="text-slate-500 mt-1 text-sm">
          Insurance regulatory intelligence — from bulletin to implementation plan.
        </p>
      </div>

      {/* Hero — empty state or stats */}
      {isEmpty ? (
        <div className="card text-center py-16">
          <div className="w-16 h-16 rounded-2xl bg-teal-50 border border-teal-100 flex items-center justify-center mx-auto mb-6">
            <Sparkles size={28} className="text-teal-500" />
          </div>
          <h2 className="text-xl font-semibold text-slate-900 mb-2">Welcome to RegShift</h2>
          <p className="text-slate-500 text-sm max-w-md mx-auto mb-8 leading-relaxed">
            Upload a regulatory bulletin, extract compliance requirements, map impacts to your
            insurance products, and generate implementation tickets — all in one workflow.
          </p>
          <div className="flex flex-col sm:flex-row gap-3 justify-center">
            <button
              id="overview-cta-upload"
              onClick={() => navigate('/documents')}
              className="btn-primary"
            >
              <FileText size={16} />
              Upload Your First Document
            </button>
            <button
              id="overview-cta-demo"
              onClick={() => navigate('/documents')}
              className="btn-secondary"
            >
              <Zap size={16} />
              Load Demo Scenario
            </button>
          </div>
        </div>
      ) : (
        <>
          {/* Stats grid */}
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
            <StatCard
              label="Documents" value={stats?.total_documents ?? 0}
              icon={FileText} color="bg-blue-500" loading={isLoading}
            />
            <StatCard
              label="Completed Analyses" value={stats?.completed_analyses ?? 0}
              icon={CheckCircle} color="bg-teal-500" loading={isLoading}
            />
            <StatCard
              label="Pending Reviews" value={stats?.pending_reviews ?? 0}
              icon={Clock} color="bg-amber-500" loading={isLoading}
            />
            <StatCard
              label="Open Tickets" value={stats?.open_tickets ?? 0}
              icon={TrendingUp} color="bg-violet-500" loading={isLoading}
            />
          </div>
        </>
      )}

      {/* Workflow explainer */}
      <div className="card">
        <h2 className="section-heading mb-4">How RegShift Works</h2>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-4">
          {[
            { step: '1', label: 'Upload Bulletin', desc: 'PDF or TXT regulatory document', icon: FileText, color: 'bg-blue-50 text-blue-600' },
            { step: '2', label: 'Extract Requirements', desc: 'AI parses structured obligations', icon: Zap, color: 'bg-teal-50 text-teal-600' },
            { step: '3', label: 'Map Impacts', desc: 'Match to your product catalogue', icon: AlertCircle, color: 'bg-amber-50 text-amber-600' },
            { step: '4', label: 'Generate Tickets', desc: 'Evidence-backed change tickets', icon: TrendingUp, color: 'bg-violet-50 text-violet-600' },
            { step: '5', label: 'Review & Approve', desc: 'Human review with audit trail', icon: CheckCircle, color: 'bg-emerald-50 text-emerald-600' },
          ].map(({ step, label, desc, icon: Icon, color }, i, arr) => (
            <div key={step} className="flex items-start gap-3">
              <div className={clsx('w-9 h-9 rounded-lg flex items-center justify-center flex-shrink-0', color)}>
                <Icon size={16} />
              </div>
              <div className="flex-1 min-w-0">
                <div className="text-xs text-slate-400 font-medium">Step {step}</div>
                <div className="text-sm font-semibold text-slate-800">{label}</div>
                <div className="text-xs text-slate-500 mt-0.5">{desc}</div>
              </div>
              {i < arr.length - 1 && (
                <ArrowRight size={14} className="text-slate-300 mt-2.5 hidden lg:block flex-shrink-0" />
              )}
            </div>
          ))}
        </div>
      </div>

      {/* Recent activity */}
      {!isEmpty && (
        <div className="card">
          <div className="flex items-center justify-between mb-4">
            <h2 className="section-heading mb-0">Recent Activity</h2>
            <button onClick={() => navigate('/audit')} className="text-xs text-teal-600 hover:text-teal-700 font-medium flex items-center gap-1">
              View all <ArrowRight size={12} />
            </button>
          </div>
          {isLoading ? (
            <div className="space-y-3">
              {[...Array(5)].map((_, i) => (
                <div key={i} className="flex gap-3">
                  <div className="skeleton w-2 h-2 rounded-full mt-1.5 flex-shrink-0" />
                  <div className="flex-1 space-y-1">
                    <div className="skeleton h-3 w-48" />
                    <div className="skeleton h-2.5 w-64" />
                  </div>
                </div>
              ))}
            </div>
          ) : stats?.recent_events.length === 0 ? (
            <p className="text-slate-400 text-sm">No activity yet.</p>
          ) : (
            <div className="space-y-3">
              {stats?.recent_events.map(event => (
                <div key={event.id} className="flex items-start gap-3 group">
                  <div className={clsx(
                    'w-2 h-2 rounded-full mt-1.5 flex-shrink-0',
                    EVENT_COLORS[event.event_type] || EVENT_COLORS.default
                  )} />
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2">
                      <span className="text-sm font-medium text-slate-800">
                        {EVENT_LABELS[event.event_type] || event.event_type}
                      </span>
                      {event.is_demo_related && (
                        <span className="badge-demo text-xs">Demo</span>
                      )}
                    </div>
                    {event.details && (
                      <p className="text-xs text-slate-500 mt-0.5 truncate">{event.details}</p>
                    )}
                  </div>
                  <span className="text-xs text-slate-400 flex-shrink-0">
                    {formatDistanceToNow(new Date(event.timestamp), { addSuffix: true })}
                  </span>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Disclaimer */}
      <div className="flex items-start gap-3 px-4 py-3 bg-amber-50 border border-amber-200 rounded-xl text-sm text-amber-800">
        <AlertCircle size={16} className="flex-shrink-0 mt-0.5 text-amber-500" />
        <p>
          <strong>Important:</strong> RegShift is a decision-support tool. It does not guarantee legal compliance,
          does not automatically modify production systems, and extractions should be reviewed by qualified
          compliance professionals before implementation.
        </p>
      </div>
    </div>
  )
}
