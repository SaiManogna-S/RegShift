import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { ScrollText, Shield, RefreshCw, ChevronLeft, ChevronRight } from 'lucide-react'
import { getAuditEvents } from '../api/client'
import { format, formatDistanceToNow } from 'date-fns'
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
  document_uploaded: 'bg-blue-400',
  analysis_started: 'bg-teal-300',
  analysis_completed: 'bg-teal-500',
  analysis_failed: 'bg-red-500',
  ticket_created: 'bg-violet-400',
  ticket_approved: 'bg-emerald-500',
  ticket_rejected: 'bg-red-400',
  ticket_changes_requested: 'bg-blue-400',
  ticket_submitted_for_review: 'bg-amber-400',
  demo_scenario_loaded: 'bg-violet-500',
  demo_scenario_reset: 'bg-slate-400',
  default: 'bg-slate-300',
}

const RECORD_TYPE_LABELS: Record<string, string> = {
  document: 'Document',
  analysis_run: 'Analysis',
  change_ticket: 'Ticket',
}

const PAGE_SIZE = 25

export default function AuditTrail() {
  const [page, setPage] = useState(0)
  const [showDemoOnly, setShowDemoOnly] = useState(false)

  const { data: events, isLoading, refetch } = useQuery({
    queryKey: ['audit', page],
    queryFn: () => getAuditEvents(100, 0), // fetch all for now
  })

  const filtered = events?.filter(e =>
    !showDemoOnly || e.is_demo_related
  ) || []

  const pageCount = Math.ceil(filtered.length / PAGE_SIZE)
  const pageEvents = filtered.slice(page * PAGE_SIZE, (page + 1) * PAGE_SIZE)

  return (
    <div className="space-y-6 animate-fade-in">
      <div>
        <h1 className="text-2xl font-bold text-slate-900">Audit Trail</h1>
        <p className="text-slate-500 mt-1 text-sm">
          Application-level log of all significant events. Read-only.
        </p>
      </div>

      {/* Disclaimer */}
      <div className="flex items-start gap-3 px-4 py-3 bg-blue-50 border border-blue-200 rounded-xl text-sm text-blue-800">
        <Shield size={16} className="flex-shrink-0 mt-0.5 text-blue-500" />
        <p>
          <strong>Audit log notice:</strong> This is an application-level event log maintained in the RegShift database.
          It is not a certified tamper-proof compliance system. Events cannot be edited or deleted through this interface.
          For regulatory compliance auditing, consult your organization's certified compliance management system.
        </p>
      </div>

      {/* Controls */}
      <div className="flex items-center gap-4">
        <label className="flex items-center gap-2 text-sm text-slate-600 cursor-pointer">
          <input
            type="checkbox"
            className="rounded"
            checked={showDemoOnly}
            onChange={e => { setShowDemoOnly(e.target.checked); setPage(0) }}
          />
          Show demo events only
        </label>
        <button className="btn-ghost" onClick={() => refetch()}>
          <RefreshCw size={14} /> Refresh
        </button>
        <span className="text-xs text-slate-400 ml-auto">
          {filtered.length} events
        </span>
      </div>

      {/* Event table */}
      <div className="card p-0 overflow-hidden">
        {isLoading ? (
          <div className="space-y-2 p-4">
            {[...Array(8)].map((_, i) => <div key={i} className="skeleton h-12 rounded" />)}
          </div>
        ) : filtered.length === 0 ? (
          <div className="text-center py-16">
            <ScrollText size={36} className="text-slate-200 mx-auto mb-3" />
            <p className="text-slate-400 text-sm">No audit events recorded yet.</p>
          </div>
        ) : (
          <>
            <table className="table-base">
              <thead>
                <tr>
                  <th className="w-8">#</th>
                  <th>Event</th>
                  <th>Type</th>
                  <th>Record</th>
                  <th>Details</th>
                  <th>Time</th>
                </tr>
              </thead>
              <tbody>
                {pageEvents.map(event => (
                  <tr key={event.id} className={event.is_demo_related ? 'bg-violet-50/30' : ''}>
                    <td className="text-slate-300 text-xs">{event.id}</td>
                    <td>
                      <div className="flex items-center gap-2">
                        <div className={clsx(
                          'w-2 h-2 rounded-full flex-shrink-0',
                          EVENT_COLORS[event.event_type] || EVENT_COLORS.default
                        )} />
                        <span className="font-medium text-slate-800 text-xs">
                          {EVENT_LABELS[event.event_type] || event.event_type}
                        </span>
                        {event.is_demo_related && (
                          <span className="badge-demo">Demo</span>
                        )}
                      </div>
                    </td>
                    <td>
                      {event.record_type && (
                        <span className="badge bg-slate-100 text-slate-500">
                          {RECORD_TYPE_LABELS[event.record_type] || event.record_type}
                        </span>
                      )}
                    </td>
                    <td className="text-slate-500 text-xs">
                      {event.record_id ? `#${event.record_id}` : '—'}
                    </td>
                    <td className="max-w-xs">
                      <p className="text-xs text-slate-500 truncate" title={event.details || ''}>
                        {event.details || '—'}
                      </p>
                    </td>
                    <td className="text-xs text-slate-400 whitespace-nowrap">
                      <span title={format(new Date(event.timestamp), 'PPpp')}>
                        {formatDistanceToNow(new Date(event.timestamp), { addSuffix: true })}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>

            {/* Pagination */}
            {pageCount > 1 && (
              <div className="flex items-center justify-between px-4 py-3 border-t border-slate-200">
                <button
                  className="btn-ghost text-xs"
                  disabled={page === 0}
                  onClick={() => setPage(p => p - 1)}
                >
                  <ChevronLeft size={14} /> Previous
                </button>
                <span className="text-xs text-slate-400">
                  Page {page + 1} of {pageCount}
                </span>
                <button
                  className="btn-ghost text-xs"
                  disabled={page >= pageCount - 1}
                  onClick={() => setPage(p => p + 1)}
                >
                  Next <ChevronRight size={14} />
                </button>
              </div>
            )}
          </>
        )}
      </div>
    </div>
  )
}
