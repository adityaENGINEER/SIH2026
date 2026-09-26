import { useEffect, useState } from 'react';
import { useProjectContext } from '../context/ProjectContext';
import { approvalsApi } from '../services/approvalsApi';
import { deliverablesApi } from '../services/deliverablesApi';
import { documentsApi } from '../services/documentsApi';
import { Approval, Deliverable, Document } from '../services/types';
import { formatTime, describeError } from '../components/common/StatusBadge';

const STATUS_LIFECYCLE = ['DRAFT', 'PENDING_HUMAN_SIGNOFF', 'APPROVED', 'REJECTED'];
const LIFECYCLE_LABELS: Record<string, string> = {
  DRAFT: 'draft', PENDING_HUMAN_SIGNOFF: 'pending sign-off', APPROVED: 'approved', REJECTED: 'rejected',
};

export function Approvals() {
  const { activeProject } = useProjectContext();
  const [filter, setFilter] = useState('all');
  const [approvals, setApprovals] = useState<Approval[]>([]);
  const [deliverables, setDeliverables] = useState<Deliverable[]>([]);
  const [documents, setDocuments] = useState<Document[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const load = async () => {
    if (!activeProject) { setApprovals([]); setDeliverables([]); return; }
    setLoading(true);
    setError(null);
    try {
      const [a, d, docs] = await Promise.all([
        approvalsApi.list(activeProject.project_id),
        deliverablesApi.list(activeProject.project_id),
        documentsApi.list(activeProject.project_id),
      ]);
      a.sort((x, y) => y.created_at.localeCompare(x.created_at));
      setApprovals(a);
      setDeliverables(d);
      setDocuments(docs);
    } catch (err) {
      setError(describeError(err, 'approval notes'));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { load(); }, [activeProject]);

  const filtered = approvals.filter(a => filter === 'all' || a.status === filter);
  const linkedIds = new Set(approvals.flatMap(a => [a.deliverable_id, ...a.output_document_ids]).filter(Boolean));
  const unlinked = deliverables.filter(d => !linkedIds.has(d.deliverable_id));
  const docName = (id: string) => documents.find(d => d.document_id === id)?.original_filename || id;

  return (
    <div style={{ padding: '24px', display: 'flex', flexDirection: 'column', gap: 24 }}>
      {/* Header */}
      <div className="page-header">
        <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', flexWrap: 'wrap', gap: 12 }}>
          <div>
            <div className="section-label" style={{ marginBottom: 6 }}>Structured Deliverables</div>
            <h1 className="font-display" style={{ fontSize: 24, fontWeight: 800, margin: 0 }}>Approval Notes</h1>
            <p style={{ margin: '6px 0 0', fontSize: 13.5, color: 'var(--muted-foreground)' }}>
              AI-generated drafts — all require human review and sign-off before finalization.
            </p>
          </div>
          <div style={{ display: 'flex', gap: 10, alignItems: 'center' }}>
            <div style={{ padding: '8px 14px', background: 'rgba(245,158,11,0.1)', border: '1px solid rgba(245,158,11,0.25)', borderRadius: 8, display: 'flex', gap: 6, alignItems: 'center' }}>
              <svg width="13" height="13" viewBox="0 0 24 24" fill="none"><path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z" stroke="#F59E0B" strokeWidth="1.5"/><line x1="12" y1="9" x2="12" y2="13" stroke="#F59E0B" strokeWidth="1.5"/><line x1="12" y1="17" x2="12.01" y2="17" stroke="#F59E0B" strokeWidth="2"/></svg>
              <span style={{ fontSize: 12, color: '#F59E0B', fontWeight: 600 }}>AI drafts — human review required</span>
            </div>
          </div>
        </div>
      </div>

      {/* Lifecycle indicator */}
      <div style={{ background: 'var(--surface-1)', border: '1px solid var(--border)', borderRadius: 12, padding: '16px 20px' }}>
        <div className="section-label" style={{ marginBottom: 12 }}>Approval Lifecycle</div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 0 }}>
          {STATUS_LIFECYCLE.map((stage, i) => (
            <div key={stage} style={{ display: 'flex', alignItems: 'center', flex: i < STATUS_LIFECYCLE.length - 1 ? 1 : 0 }}>
              <div style={{
                display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 5,
              }}>
                <div style={{
                  width: 28, height: 28, borderRadius: '50%',
                  background: stage === 'APPROVED' ? 'rgba(16,185,129,0.2)' :
                    stage === 'REJECTED' ? 'rgba(239,68,68,0.2)' :
                    stage === 'PENDING_HUMAN_SIGNOFF' ? 'rgba(245,158,11,0.2)' : 'var(--surface-2)',
                  border: `1.5px solid ${stage === 'APPROVED' ? 'var(--green)' :
                    stage === 'REJECTED' ? 'var(--red)' :
                    stage === 'PENDING_HUMAN_SIGNOFF' ? 'var(--amber)' : 'var(--border)'}`,
                  display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 13,
                }}>
                  {stage === 'DRAFT' ? '📝' : stage === 'PENDING_HUMAN_SIGNOFF' ? '👤' : stage === 'APPROVED' ? '✓' : '✗'}
                </div>
                <span style={{ fontSize: 10.5, color: 'var(--muted-foreground)', textTransform: 'capitalize', whiteSpace: 'nowrap', fontFamily: 'JetBrains Mono' }}>
                  {LIFECYCLE_LABELS[stage]} ({approvals.filter(a => a.status === stage).length})
                </span>
              </div>
              {i < STATUS_LIFECYCLE.length - 1 && (
                <div style={{ flex: 1, height: 1.5, background: 'var(--border)', margin: '0 8px', marginBottom: 18 }} />
              )}
            </div>
          ))}
        </div>
      </div>

      {/* Filter */}
      <div className="tab-bar" style={{ alignSelf: 'flex-start' }}>
        {[
          { key: 'all', label: 'All' },
          { key: 'DRAFT', label: 'Draft' },
          { key: 'PENDING_HUMAN_SIGNOFF', label: 'Pending Review' },
          { key: 'APPROVED', label: 'Approved' },
          { key: 'REJECTED', label: 'Rejected' },
        ].map(f => (
          <button key={f.key} onClick={() => setFilter(f.key)} className={`tab-item ${filter === f.key ? 'active' : ''}`}>
            {f.label}
          </button>
        ))}
      </div>

      {error && (
        <div style={{ padding: '10px 14px', borderRadius: 8, border: '1px solid rgba(239,68,68,0.4)', background: 'rgba(239,68,68,0.08)', color: '#F87171', fontSize: 12.5 }}>
          {error} <button className="btn-ghost" style={{ fontSize: 12, marginLeft: 8 }} onClick={load}>Retry</button>
        </div>
      )}

      {/* Approval notes list */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
        {!activeProject && <p style={{ color: 'var(--muted-foreground)', fontSize: 13.5 }}>Select a project to view its approval notes.</p>}
        {activeProject && loading && approvals.length === 0 && <p style={{ color: 'var(--muted-foreground)', fontSize: 13.5 }}>Loading approval notes…</p>}
        {activeProject && !loading && !error && filtered.length === 0 && (
          <p style={{ color: 'var(--muted-foreground)', fontSize: 13.5 }}>No approval notes{filter !== 'all' ? ' with this status' : ''} in this project.</p>
        )}
        {activeProject && filtered.map(appr => (
          <ApprovalCard
            key={appr.approval_id}
            projectId={activeProject.project_id}
            approval={appr}
            deliverables={deliverables.filter(d => d.approval_id === appr.approval_id || appr.output_document_ids.includes(d.deliverable_id) || d.deliverable_id === appr.deliverable_id)}
            docName={docName}
            onChanged={load}
          />
        ))}
      </div>

      {activeProject && unlinked.length > 0 && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
          <div className="section-label">Deliverables without approval record</div>
          {unlinked.map(d => (
            <div key={d.deliverable_id} className="card-glass" style={{ borderRadius: 12, padding: '14px 20px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <span style={{ fontSize: 13 }}>{d.filename} <span className="font-mono" style={{ fontSize: 11, color: 'var(--muted-foreground)' }}>· {formatTime(d.created_at)}</span></span>
              <a className="btn-secondary" style={{ fontSize: 12, padding: '6px 16px' }} href={deliverablesApi.getDownloadUrl(activeProject.project_id, d.deliverable_id)}>↓ {d.type}</a>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

function ApprovalCard({ projectId, approval, deliverables, docName, onChanged }: {
  projectId: string; approval: Approval; deliverables: Deliverable[]; docName: (id: string) => string; onChanged: () => void;
}) {
  const [approverName, setApproverName] = useState('');
  const [employeeId, setEmployeeId] = useState('');
  const [reason, setReason] = useState('');
  const [busy, setBusy] = useState(false);
  const [actionError, setActionError] = useState<string | null>(null);

  const act = async (action: 'submit' | 'approve' | 'reject') => {
    setActionError(null);
    if (action !== 'submit' && (!approverName.trim() || !employeeId.trim())) {
      setActionError('Approver name and employee ID are required for a human decision.');
      return;
    }
    if (action === 'reject' && !reason.trim()) {
      setActionError('A rejection reason is required.');
      return;
    }
    setBusy(true);
    try {
      const decision = { approver_name: approverName.trim(), employee_id: employeeId.trim(), reason: reason.trim() || undefined };
      if (action === 'submit') await approvalsApi.submitReview(projectId, approval.approval_id);
      if (action === 'approve') await approvalsApi.approve(projectId, approval.approval_id, decision);
      if (action === 'reject') await approvalsApi.reject(projectId, approval.approval_id, decision);
      onChanged();
    } catch (err: any) {
      setActionError(describeError(err, 'approval action').replace('Failed to load approval action', 'Action failed'));
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="card-glass" style={{ borderRadius: 12, padding: '18px 20px' }}>
      <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', marginBottom: 12, flexWrap: 'wrap', gap: 10 }}>
        <div>
          <div style={{ display: 'flex', gap: 8, alignItems: 'center', marginBottom: 5 }}>
            <span className="font-mono" style={{ fontSize: 12, color: 'var(--muted-foreground)' }}>{approval.approval_id}</span>
            {approval.task_id && <>
              <span className="font-mono" style={{ fontSize: 11, color: 'var(--muted-foreground)' }}>·</span>
              <span className="font-mono" style={{ fontSize: 11.5, color: 'var(--muted-foreground)' }}>{approval.task_id}</span>
            </>}
          </div>
          <div className="font-display" style={{ fontSize: 16, fontWeight: 700 }}>{approval.title}</div>
          <div style={{ fontSize: 12, color: 'var(--muted-foreground)', marginTop: 3 }}>
            Created {formatTime(approval.created_at)}
            {approval.submitted_at && <> · Submitted {formatTime(approval.submitted_at)}</>}
            {approval.reviewed_at && <> · Reviewed {formatTime(approval.reviewed_at)}</>}
          </div>
          {approval.source_document_ids.length > 0 && (
            <div style={{ fontSize: 12, color: 'var(--muted-foreground)', marginTop: 3 }}>Sources: {approval.source_document_ids.map(docName).join(', ')}</div>
          )}
          {approval.approver_name && (
            <div style={{ fontSize: 12, color: 'var(--foreground)', marginTop: 3 }}>
              Reviewer: {approval.approver_name} ({approval.employee_id}) · signature {approval.signature_status}
              {approval.review_comment && <> · “{approval.review_comment}”</>}
            </div>
          )}
          {approval.rejection_reason && <div style={{ fontSize: 12, color: '#F87171', marginTop: 3 }}>Rejection reason: {approval.rejection_reason}</div>}
          {approval.approval_reason && <div style={{ fontSize: 12, color: 'var(--foreground)', marginTop: 3 }}>Approval note: {approval.approval_reason}</div>}
        </div>
        <ApprovalStatus status={approval.status} />
      </div>

      {/* Download buttons — only files that actually exist */}
      <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
        {deliverables.length === 0 && <span style={{ fontSize: 12, color: 'var(--muted-foreground)' }}>No deliverable files linked.</span>}
        {deliverables.map((d, i) => (
          <a key={d.deliverable_id} href={deliverablesApi.getDownloadUrl(projectId, d.deliverable_id)}
            className={i === 0 ? 'btn-primary' : 'btn-secondary'} style={{ fontSize: 12, padding: '6px 16px' }}>
            ↓ {d.type}
          </a>
        ))}
      </div>

      {(approval.status === 'DRAFT' || approval.status === 'PENDING_HUMAN_SIGNOFF') && (
        <div style={{ marginTop: 14, display: 'flex', gap: 8, flexWrap: 'wrap', alignItems: 'center' }}>
          {approval.status === 'DRAFT' && (
            <button className="btn-secondary" style={{ fontSize: 12, padding: '6px 14px' }} disabled={busy} onClick={() => act('submit')}>Submit for human sign-off</button>
          )}
          {approval.status === 'PENDING_HUMAN_SIGNOFF' && <>
            <input className="input-field" style={{ width: 160, fontSize: 12 }} placeholder="Approver name" value={approverName} onChange={e => setApproverName(e.target.value)} />
            <input className="input-field" style={{ width: 120, fontSize: 12 }} placeholder="Employee ID" value={employeeId} onChange={e => setEmployeeId(e.target.value)} />
            <input className="input-field" style={{ width: 200, fontSize: 12 }} placeholder="Reason / comment" value={reason} onChange={e => setReason(e.target.value)} />
            <button className="btn-primary" style={{ fontSize: 12, padding: '6px 14px' }} disabled={busy} onClick={() => act('approve')}>Approve</button>
            <button className="btn-secondary" style={{ fontSize: 12, padding: '6px 14px', color: '#EF4444' }} disabled={busy} onClick={() => act('reject')}>Reject</button>
          </>}
        </div>
      )}
      {actionError && <div style={{ marginTop: 8, fontSize: 12, color: '#F87171' }}>{actionError}</div>}
    </div>
  );
}

function ApprovalStatus({ status }: { status: string }) {
  const cfg: Record<string, { cls: string; label: string; icon: string }> = {
    'DRAFT': { cls: 'badge-gray', label: 'Draft', icon: '📝' },
    'PENDING_HUMAN_SIGNOFF': { cls: 'badge-amber', label: 'Pending Human Sign-off', icon: '👤' },
    'APPROVED': { cls: 'badge-green', label: 'Approved', icon: '✓' },
    'REJECTED': { cls: 'badge-red', label: 'Rejected', icon: '✗' },
  };
  const { cls, label, icon } = cfg[status] || { cls: 'badge-gray', label: status, icon: '•' };
  return (
    <span className={`badge ${cls}`} style={{ fontSize: 12, padding: '4px 12px' }}>
      {icon} {label}
    </span>
  );
}
