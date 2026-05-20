import React, { useState, useRef, useEffect, useCallback } from 'react'
import { createPortal } from 'react-dom'
import { cn } from '@/lib/utils'
import { ChevronDown } from 'lucide-react'

interface SelectOption {
  label: string
  value: any
}

interface CustomSelectProps {
  value: any
  options: SelectOption[]
  onChange: (value: any) => void
  placeholder?: string
}

export const CustomSelect = ({ value, options, onChange, placeholder }: CustomSelectProps) => {
  const [isOpen, setIsOpen] = useState(false)
  const [dropdownStyle, setDropdownStyle] = useState<React.CSSProperties>({})
  const triggerRef = useRef<HTMLDivElement>(null)
  const dropdownRef = useRef<HTMLDivElement>(null)

  // Store label on select so trigger always shows correct text immediately,
  // independent of whether the options array is still populated.
  const [localLabel, setLocalLabel] = useState<string | null>(null)

  // Clear local label when value is reset externally (parent clears the field)
  const prevValueRef = useRef(value)
  if (prevValueRef.current !== value) {
    prevValueRef.current = value
    if (!value) setLocalLabel(null)
  }

  const computePosition = useCallback(() => {
    if (!triggerRef.current) return
    const rect = triggerRef.current.getBoundingClientRect()
    const spaceBelow = window.innerHeight - rect.bottom
    const spaceAbove = rect.top
    const dropdownH = Math.min((options.length || 1) * 32 + 8, 240)

    if (spaceBelow >= dropdownH || spaceBelow >= spaceAbove) {
      setDropdownStyle({
        top: rect.bottom + 4,
        left: rect.left,
        width: rect.width,
        maxHeight: Math.min(dropdownH, spaceBelow - 8),
      })
    } else {
      setDropdownStyle({
        bottom: window.innerHeight - rect.top + 4,
        left: rect.left,
        width: rect.width,
        maxHeight: Math.min(dropdownH, spaceAbove - 8),
      })
    }
  }, [options.length])

  const open = () => {
    computePosition()
    setIsOpen(true)
  }

  // Recompute position on scroll/resize while open
  useEffect(() => {
    if (!isOpen) return
    const handler = () => computePosition()
    window.addEventListener('scroll', handler, true)
    window.addEventListener('resize', handler)
    return () => {
      window.removeEventListener('scroll', handler, true)
      window.removeEventListener('resize', handler)
    }
  }, [isOpen, computePosition])

  // Close on outside mousedown — but exclude the portal dropdown itself.
  // Without this exclusion, mousedown on an option closes the portal BEFORE
  // the click event fires, so onChange never gets called.
  useEffect(() => {
    if (!isOpen) return
    const handler = (e: MouseEvent) => {
      const target = e.target as Node
      if (
        !triggerRef.current?.contains(target) &&
        !dropdownRef.current?.contains(target)
      ) {
        setIsOpen(false)
      }
    }
    document.addEventListener('mousedown', handler)
    return () => document.removeEventListener('mousedown', handler)
  }, [isOpen])

  const selectedOption = options?.find((o) => o.value === value)
  const displayText =
    selectedOption?.label ??
    localLabel ??
    (value ? String(value) : null) ??
    placeholder ??
    'Select...'
  const hasValue = !!(selectedOption || localLabel || value)

  return (
    <div className="relative" ref={triggerRef}>
      <div
        onClick={open}
        className="w-full bg-surface-editor border border-border rounded-md px-3 h-[32px] flex items-center justify-between cursor-pointer hover:border-border-strong transition-all"
      >
        <span className={cn('text-[12px]', hasValue ? 'text-white' : 'text-text-muted')}>
          {displayText}
        </span>
        <ChevronDown className="w-3.5 h-3.5 text-text-muted shrink-0" />
      </div>

      {isOpen && createPortal(
        <div
          ref={dropdownRef}
          className="fixed bg-surface-editor border border-border rounded-md shadow-xl z-[9999] overflow-y-auto py-1 custom-scrollbar"
          style={dropdownStyle}
        >
          {options?.map((opt) => (
            <div
              key={opt.value}
              onClick={() => {
                setLocalLabel(opt.label)
                onChange(opt.value)
                setIsOpen(false)
              }}
              className={cn(
                'px-3 py-1.5 text-[12px] cursor-pointer transition-colors',
                opt.value === value ? 'text-white bg-surface-5' : 'text-white hover:bg-surface-5'
              )}
            >
              {opt.label}
            </div>
          ))}
          {(!options || options.length === 0) && (
            <div className="px-3 py-2 text-[12px] text-text-muted">No options</div>
          )}
        </div>,
        document.body
      )}
    </div>
  )
}
