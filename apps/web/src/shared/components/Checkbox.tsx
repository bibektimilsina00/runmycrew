import { type ChangeEvent } from 'react'
import { Checkbox as RadixCheckbox } from '@/components/ui/checkbox'
import { cn } from '@/lib/cn'

interface CheckboxProps {
  checked?: boolean
  onChange?: (e: ChangeEvent<HTMLInputElement>) => void
  label?: string
  className?: string
  id?: string
}

export function Checkbox({ checked = false, onChange, label, className, id }: CheckboxProps) {
  const inputId = id ?? (label ? `cb-${label.toLowerCase().replace(/\s+/g, '-')}` : undefined)

  const handleCheckedChange = (val: boolean | 'indeterminate') => {
    if (onChange) {
      const isChecked = val === true
      const event = {
        target: {
          checked: isChecked,
          type: 'checkbox',
        },
        currentTarget: {
          checked: isChecked,
        },
      } as unknown as ChangeEvent<HTMLInputElement>
      onChange(event)
    }
  }

  return (
    <label
      htmlFor={inputId}
      className={cn('group inline-flex items-center gap-[7px] cursor-pointer select-none', className)}
    >
      <RadixCheckbox
        id={inputId}
        checked={checked}
        onCheckedChange={handleCheckedChange}
      />
      {label && (
        <span className="text-[13px] text-text-mute group-hover:text-text transition-colors [transition-duration:120ms] leading-none">
          {label}
        </span>
      )}
    </label>
  )
}
