import { useState } from 'react'
import { Icons } from '@/shared/components/icons'
import type { WorkspaceRole } from '../types/workspaceTypes'
import { cn } from '@/lib/cn'
import { Dropdown, DropdownTrigger, DropdownContent, DropdownItem } from '@/shared/components'

const ROLE_LABELS: Record<WorkspaceRole, string> = {
  owner: 'Owner',
  admin: 'Admin',
  member: 'Member',
  viewer: 'Viewer',
}

const ROLE_DESCS: Record<WorkspaceRole, string> = {
  owner: 'Full control',
  admin: 'Can manage members',
  member: 'Can view & edit',
  viewer: 'Read-only',
}

interface Props {
  value: WorkspaceRole
  options: WorkspaceRole[]
  onChange: (role: WorkspaceRole) => void
  disabled?: boolean
  className?: string
}

export function RoleSelect({ value, options, onChange, disabled, className }: Props) {
  const [open, setOpen] = useState(false)

  const handleSelect = (role: WorkspaceRole) => {
    onChange(role)
  }

  return (
    <Dropdown open={open} onOpenChange={setOpen} className={className}>
      <DropdownTrigger disabled={disabled}>
        <button
          className={cn(
            "inline-flex items-center gap-[6px] px-[9px] py-[5px] pl-[8px] rounded-[7px]",
            "bg-[var(--surface)] border border-[var(--border-faint)] text-[12px] font-medium",
            "transition-colors duration-100 outline-none justify-between",
            disabled 
              ? "opacity-50 cursor-default" 
              : "cursor-pointer hover:bg-[var(--surface-2)] hover:border-[var(--border-soft)]",
            "group"
          )}
          type="button"
          disabled={disabled}
        >
          <span className={cn(
            "text-[var(--text-mute)]",
            value === 'admin' && "text-[var(--accent)]",
            value === 'member' && "text-[var(--text-mute)]",
            value === 'viewer' && "text-[var(--text-dim)]"
          )}>{ROLE_LABELS[value]}</span>
          <Icons.Caret style={{ width: 10, height: 10, color: 'var(--text-faint)', transition: 'transform 120ms', transform: open ? 'rotate(180deg)' : 'rotate(0deg)' }} />
        </button>
      </DropdownTrigger>

      <DropdownContent
        className="bg-[var(--bg-2)] border border-[var(--border)] rounded-[11px] p-[5px] shadow-[0_16px_40px_-12px_oklch(0_0_0/0.6)] animate-in fade-in slide-in-from-top-1 flex flex-col gap-[2px] min-w-[180px]"
      >
        {options.map(role => (
          <DropdownItem
            key={role}
            className={cn(
              "flex items-center gap-[10px] w-full px-[10px] py-[8px] rounded-[7px] bg-transparent border-none cursor-pointer transition-colors duration-75 hover:bg-[var(--surface)]",
              role === value && "bg-[var(--surface)]"
            )}
            onClick={() => handleSelect(role)}
          >
            <span className="flex items-center gap-[8px] flex-1">
              <span className={cn(
                "w-[7px] h-[7px] rounded-full shrink-0",
                role === 'owner' && "bg-[var(--ok)]",
                role === 'admin' && "bg-[var(--accent)]",
                role === 'member' && "bg-[var(--text-mute)]",
                role === 'viewer' && "bg-[var(--text-dim)]"
              )} />
              <span className="text-[13px] font-medium text-[var(--text)]">{ROLE_LABELS[role]}</span>
            </span>
            <span className="text-[11.5px] text-[var(--text-faint)] font-mono">{ROLE_DESCS[role]}</span>
            {role === value && <Icons.Check style={{ width: 12, height: 12, color: 'var(--ok)', flexShrink: 0 }} />}
          </DropdownItem>
        ))}
      </DropdownContent>
    </Dropdown>
  )
}
