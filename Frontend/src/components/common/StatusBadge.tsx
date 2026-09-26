const STATUS_CLASSES: Record<string, string> = {
  completed: 'badge-green',
  approved: 'badge-teal',
  ready: 'badge-green',
  failed: 'badge-red',
  rejected: 'badge-red',
  cancelled: 'badge-gray',
  draft: 'badge-gray',
  pending_human_signoff: 'badge-amber',
  queued: 'badge-gray',
  planning: 'badge-violet',
  executing: 'badge-violet',
  observing: 'badge-violet',
  validating: 'badge-violet',
  replanning: 'badge-amber',
  running: 'badge-violet',
  pending: 'badge-gray',
};

export function statusLabel(status: string): string {
  if (status.toUpperCase() === 'PENDING_HUMAN_SIGNOFF') return 'Pending Human Sign-off';
  return status.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase());
}

export function StatusBadge({ status, size }: { status: string; size?: 'lg' }) {
  const cls = STATUS_CLASSES[status.toLowerCase()] || 'badge-gray';
  return <span className={`badge ${cls}`} style={{ fontSize: size === 'lg' ? 12 : 10.5 }}>{statusLabel(status)}</span>;
}

export function formatTime(iso?: string | null): string {
  if (!iso) return '—';
  const d = new Date(iso);
  return isNaN(d.getTime()) ? '—' : d.toLocaleString();
}

export function describeError(err: any, what: string): string {
  if (err instanceof TypeError) return `Backend unavailable — could not load ${what}.`;
  const detail = err?.data?.detail;
  const message = detail?.error?.message || detail?.message || err?.message;
  return `Failed to load ${what}: ${message || 'unknown error'}`;
}
