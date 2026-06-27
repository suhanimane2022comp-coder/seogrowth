import clsx from 'clsx'
import { Clock, Loader2, CheckCircle2, XCircle } from 'lucide-react'

interface Props { status: string }

const map: Record<string, { label: string; cls: string; Icon: any }> = {
  pending:   { label: 'Pending',    cls: 'bg-slate-100 text-slate-600',   Icon: Clock },
  running:   { label: 'Analyzing…', cls: 'bg-blue-100 text-blue-700',     Icon: Loader2 },
  completed: { label: 'Completed',  cls: 'bg-emerald-100 text-emerald-700', Icon: CheckCircle2 },
  failed:    { label: 'Failed',     cls: 'bg-red-100 text-red-700',       Icon: XCircle },
}

export default function StatusBadge({ status }: Props) {
  const { label, cls, Icon } = map[status] ?? map.pending
  return (
    <span className={clsx('inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold', cls)}>
      <Icon className={clsx('w-3.5 h-3.5', status === 'running' && 'animate-spin')} />
      {label}
    </span>
  )
}
