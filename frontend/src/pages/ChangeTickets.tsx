import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import {
  Ticket, CheckCircle, XCircle, MessageSquare, ChevronDown, ChevronUp,
  Clock, AlertCircle, Edit3, Send, Loader2
} from 'lucide-react'
import {
  listTickets, reviewTicket, submitTicketForReview
} from '../api/client'
import type { ChangeTicket, ReviewAction } from '../types'
import { format, formatDistanceToNow } from 'date-fns'
import toast from 'react-hot-toast'
import clsx from 'clsx'

const STATUS_CONFIG: Record<string, { label: string; cls: string; icon: any }> = {
  draft: { label: 'Draft', cls: 'badge-draft', icon: Edit3 },
  pending_review: { label: 'Pending Review', cls: 'badge-pending', icon: Clock },
  approved: { label: 'Approved', cls: 'badge-approved', icon: CheckCircle },
  rejected: { label: 'Rejected', cls: 'badge-rejected', icon: XCircle },
  changes_requested: { label: 'Changes Requested', cls: 'badge-changes', icon: MessageSquare },
}

const PRIORITY_CONFIG: Record<string, { cls: string; label: string }> = {
  critical: { cls: 'badge-critical', label: 'Critical' },
  high: { cls: 'badge-high', label: 'High' },
  medium: { cls: 'badge-medium', label: 'Medium' },
  low: { cls: 'badge-low', label: 'Low' },
}

function TicketStatusBadge({ status }: { status: string }) {
  const cfg = STATUS_CONFIG[status] || { label: status, cls: 'badge-draft', icon: Clock }
  const Icon = cfg.icon
  return (
    <span className={clsx('badge gap-1', cfg.cls)}>
      <Icon size={10} />
      {cfg.label}
    </span>
  )
}

function PriorityBadge({ priority }: { priority: string }) {
  const cfg = PRIORITY_CONFIG[priority] || { cls: 'badge-low', label: priority }
  return <span className={clsx('badge', cfg.cls)}>{cfg.label}</span>
}

function ReviewModal({
  ticket,
  action,
  onClose,
  onSubmit,
}: {
  ticket: ChangeTicket
  action: 'approve' | 'reject' | 'request_changes'
  onClose: () => void
  onSubmit: (comment: string) => void
}) {
  const [comment, setComment] = useState('')
  const labels = {
    approve: { title: 'Approve Ticket', btn: 'Approve', color: 'bg-emerald-500 hover:bg-emerald-600' },
    reject: { title: 'Reject Ticket', btn: 'Reject', color: 'bg-red-500 hover:bg-red-600' },
    request_changes: { title: 'Request Changes', btn: 'Request Changes', color: 'bg-blue-500 hover:bg-blue-600' },
  }[action]

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 px-4 animate-fade-in">
      <div className="bg-white rounded-2xl shadow-2xl w-full max-w-lg animate-slide-up">
        <div className="px-6 py-5 border-b border-slate-200">
          <h3 className="font-semibold text-slate-900">{labels.title}</h3>
          <p className="text-sm text-slate-500 mt-0.5">{ticket.ticket_ref} — {ticket.title}</p>
        </div>
        <div className="px-6 py-5 space-y-4">
          <div>
            <label className="text-xs font-semibold text-slate-500 uppercase tracking-wide mb-1.5 block">
              Reviewer Comment {action !== 'approve' && '(Required)'}
            </label>
            <textarea
              className="textarea h-28"
              placeholder={
                action === 'approve' ? 'Optional approval note…' :
                action === 'reject' ? 'Explain why this ticket is being rejected…' :
                'Describe what changes are needed…'
              }
              value={comment}
              onChange={e => setComment(e.target.value)}
              autoFocus
            />
          </div>
          {action !== 'approve' && !comment.trim() && (
            <p className="text-xs text-amber-600">A comment is recommended for this action.</p>
          )}
        </div>
        <div className="px-6 py-4 border-t border-slate-200 flex gap-3 justify-end">
          <button className="btn-secondary" onClick={onClose}>Cancel</button>
          <button
            className={clsx('inline-flex items-center gap-2 px-5 py-2.5 text-white font-semibold text-sm rounded-lg transition-all', labels.color)}
            onClick={() => onSubmit(comment)}
          >
            {labels.btn}
          </button>
        </div>
      </div>
    </div>
  )
}

function TicketCard({ ticket }: { ticket: ChangeTicket }) {
  const [expanded, setExpanded] = useState(false)
  const [reviewAction, setReviewAction] = useState<'approve' | 'reject' | 'request_changes' | null>(null)
  const queryClient = useQueryClient()

  const reviewMutation = useMutation({
    mutationFn: (body: ReviewAction) => reviewTicket(ticket.id, body),
    onSuccess: (updated) => {
      queryClient.invalidateQueries({ queryKey: ['tickets'] })
      queryClient.invalidateQueries({ queryKey: ['overview-stats'] })
      toast.success(`Ticket ${updated.ticket_ref} ${updated.status.replace('_', ' ')}`)
      setReviewAction(null)
    },
    onError: (e: any) => {
      toast.error(e?.response?.data?.detail || 'Review action failed')
    },
  })

  const submitMutation = useMutation({
    mutationFn: () => submitTicketForReview(ticket.id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['tickets'] })
      queryClient.invalidateQueries({ queryKey: ['overview-stats'] })
      toast.success('Ticket submitted for review')
    },
    onError: (e: any) => toast.error(e?.response?.data?.detail || 'Submit failed'),
  })


  return (
    <>
      {reviewAction && (
        <ReviewModal
          ticket={ticket}
          action={reviewAction}
          onClose={() => setReviewAction(null)}
          onSubmit={(comment) => reviewMutation.mutate({ action: reviewAction, comment })}
        />
      )}

      <div className="border border-slate-200 rounded-xl overflow-hidden hover:border-slate-300 transition-colors">
        <div
          className="flex items-start gap-4 p-5 cursor-pointer"
          onClick={() => setExpanded(!expanded)}
        >
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2 flex-wrap mb-2">
              <span className="text-xs font-mono font-bold text-slate-400">{ticket.ticket_ref}</span>
              <TicketStatusBadge status={ticket.status} />
              <PriorityBadge priority={ticket.priority} />
              {ticket.is_demo && <span className="badge-demo">Demo</span>}
            </div>
            <h3 className="text-sm font-semibold text-slate-900 leading-snug">{ticket.title}</h3>
            {ticket.effective_date && (
              <p className="text-xs text-amber-600 mt-1">Effective: {ticket.effective_date}</p>
            )}
            <p className="text-xs text-slate-400 mt-1.5">
              Created {formatDistanceToNow(new Date(ticket.created_at), { addSuffix: true })}
            </p>
          </div>

          {/* Actions */}
          <div className="flex items-center gap-2 flex-shrink-0" onClick={e => e.stopPropagation()}>
            {ticket.status === 'draft' && (
              <button
                id={`submit-ticket-${ticket.id}`}
                className="btn-secondary text-xs py-1.5 px-3"
                onClick={() => submitMutation.mutate()}
                disabled={submitMutation.isPending}
              >
                {submitMutation.isPending ? <Loader2 size={12} className="animate-spin" /> : <Send size={12} />}
                Submit
              </button>
            )}
            {ticket.status === 'pending_review' && (
              <>
                <button
                  id={`approve-ticket-${ticket.id}`}
                  className="btn-primary text-xs py-1.5 px-3"
                  onClick={() => setReviewAction('approve')}
                >
                  <CheckCircle size={12} /> Approve
                </button>
                <button
                  id={`reject-ticket-${ticket.id}`}
                  className="btn-secondary text-xs py-1.5 px-3 text-red-600 hover:text-red-700"
                  onClick={() => setReviewAction('reject')}
                >
                  <XCircle size={12} /> Reject
                </button>
                <button
                  id={`changes-ticket-${ticket.id}`}
                  className="btn-ghost text-xs"
                  onClick={() => setReviewAction('request_changes')}
                >
                  <MessageSquare size={12} /> Changes
                </button>
              </>
            )}
          </div>

          {expanded ? <ChevronUp size={16} className="text-slate-400 flex-shrink-0" /> : <ChevronDown size={16} className="text-slate-400 flex-shrink-0" />}
        </div>

        {expanded && (
          <div className="border-t border-slate-100 px-5 pb-5 pt-4 space-y-5 bg-slate-50/30">
            {/* Reviewer comment */}
            {ticket.reviewer_comment && (
              <div className="flex gap-2 p-3 bg-blue-50 border border-blue-200 rounded-lg">
                <MessageSquare size={14} className="text-blue-500 flex-shrink-0 mt-0.5" />
                <div>
                  <div className="text-xs font-semibold text-blue-700 mb-0.5">Reviewer Comment</div>
                  <p className="text-sm text-blue-700">{ticket.reviewer_comment}</p>
                </div>
              </div>
            )}

            {/* Proposed action */}
            <div>
              <div className="text-xs font-semibold text-slate-500 uppercase tracking-wide mb-2">Proposed Implementation Action</div>
              <p className="text-sm text-slate-700 whitespace-pre-line">{ticket.proposed_action}</p>
            </div>

            {/* Evidence */}
            <div>
              <div className="text-xs font-semibold text-slate-500 uppercase tracking-wide mb-2">Supporting Evidence</div>
              <div className="p-3 bg-white border border-slate-200 rounded-lg">
                <pre className="text-xs text-slate-600 whitespace-pre-wrap font-sans leading-relaxed">{ticket.evidence}</pre>
              </div>
            </div>

            {/* Priority rationale */}
            <div>
              <div className="text-xs font-semibold text-slate-500 uppercase tracking-wide mb-1">Priority Rationale</div>
              <p className="text-sm text-slate-600">{ticket.priority_rationale}</p>
            </div>

            {/* Assumptions */}
            {ticket.assumptions && (
              <div className="flex gap-2 p-3 bg-amber-50 border border-amber-200 rounded-lg">
                <AlertCircle size={14} className="text-amber-500 flex-shrink-0 mt-0.5" />
                <div>
                  <div className="text-xs font-semibold text-amber-700 mb-0.5">Assumptions & Unresolved Questions</div>
                  <p className="text-sm text-amber-700">{ticket.assumptions}</p>
                </div>
              </div>
            )}

            <div className="flex gap-4 text-xs text-slate-400">
              <span>ID: {ticket.id}</span>
              <span>·</span>
              <span>Created: {format(new Date(ticket.created_at), 'MMM d, yyyy HH:mm')}</span>
              <span>·</span>
              <span>Updated: {format(new Date(ticket.updated_at), 'MMM d, yyyy HH:mm')}</span>
            </div>
          </div>
        )}
      </div>
    </>
  )
}

const STATUS_FILTERS = [
  { value: 'all', label: 'All Tickets' },
  { value: 'draft', label: 'Draft' },
  { value: 'pending_review', label: 'Pending Review' },
  { value: 'approved', label: 'Approved' },
  { value: 'rejected', label: 'Rejected' },
  { value: 'changes_requested', label: 'Changes Requested' },
]

export default function ChangeTickets() {
  const [statusFilter, setStatusFilter] = useState('all')

  const { data: tickets, isLoading } = useQuery({
    queryKey: ['tickets'],
    queryFn: listTickets,
  })

  const filtered = tickets?.filter(t =>
    statusFilter === 'all' || t.status === statusFilter
  ) || []

  return (
    <div className="space-y-6 animate-fade-in">
      <div>
        <h1 className="text-2xl font-bold text-slate-900">Change Tickets</h1>
        <p className="text-slate-500 mt-1 text-sm">
          Track regulatory implementation tasks from draft through approval.
        </p>
      </div>

      {/* Filter tabs */}
      <div className="flex gap-1 p-1 bg-slate-100 rounded-lg w-fit flex-wrap">
        {STATUS_FILTERS.map(f => (
          <button
            key={f.value}
            onClick={() => setStatusFilter(f.value)}
            className={clsx(
              'px-3 py-1.5 rounded-md text-xs font-medium transition-all duration-150',
              statusFilter === f.value
                ? 'bg-white text-slate-900 shadow-sm'
                : 'text-slate-500 hover:text-slate-700'
            )}
          >
            {f.label}
            {f.value !== 'all' && tickets && (
              <span className="ml-1.5 text-slate-400">
                ({tickets.filter(t => t.status === f.value).length})
              </span>
            )}
          </button>
        ))}
      </div>

      {isLoading ? (
        <div className="space-y-3">
          {[...Array(3)].map((_, i) => <div key={i} className="skeleton h-24 rounded-xl" />)}
        </div>
      ) : filtered.length === 0 ? (
        <div className="card text-center py-14">
          <Ticket size={36} className="text-slate-200 mx-auto mb-3" />
          <p className="text-slate-600 font-medium">No tickets found</p>
          <p className="text-slate-400 text-sm mt-1">
            {statusFilter === 'all'
              ? 'Create tickets from the Impact Analysis page after running an analysis.'
              : `No ${statusFilter.replace('_', ' ')} tickets.`}
          </p>
        </div>
      ) : (
        <div className="space-y-3">
          {filtered.map(ticket => (
            <TicketCard key={ticket.id} ticket={ticket} />
          ))}
        </div>
      )}
    </div>
  )
}
