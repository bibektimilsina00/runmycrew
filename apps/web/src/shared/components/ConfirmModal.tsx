import { createContext, useContext, useState, useRef, type ReactNode } from 'react'
import { Modal } from './Modal'
import { Button } from './Button'
import { logger } from '@/shared/utils/logger'

export interface ConfirmOptions {
  title?: string
  message: string
  confirmText?: string
  cancelText?: string
  variant?: 'danger' | 'primary' | 'secondary'
}

interface ConfirmContextValue {
  confirm: (options: ConfirmOptions) => Promise<boolean>
}

const ConfirmContext = createContext<ConfirmContextValue | null>(null)

// eslint-disable-next-line react-refresh/only-export-components
export function useConfirm() {
  const context = useContext(ConfirmContext)
  if (!context) {
    throw new Error('useConfirm must be used within a ConfirmProvider')
  }
  return context.confirm
}

export function ConfirmProvider({ children }: { children: ReactNode }) {
  const [open, setOpen] = useState(false)
  const [options, setOptions] = useState<ConfirmOptions | null>(null)
  const resolveRef = useRef<((value: boolean) => void) | null>(null)

  const confirm = (opts: ConfirmOptions) => {
    logger.info('confirm dialog requested with options:', opts)
    return new Promise<boolean>((resolve) => {
      setOptions(opts)
      setOpen(true)
      resolveRef.current = resolve
    })
  }

  const handleCancel = () => {
    logger.info('confirm cancel clicked')
    setOpen(false)
    resolveRef.current?.(false)
    resolveRef.current = null
  }

  const handleConfirm = () => {
    logger.info('confirm approve clicked')
    setOpen(false)
    resolveRef.current?.(true)
    resolveRef.current = null
  }

  const footer = (
    <>
      <Button variant="secondary" size="sm" onClick={handleCancel}>
        {options?.cancelText ?? 'Cancel'}
      </Button>
      <Button
        variant={options?.variant ?? 'danger'}
        size="sm"
        onClick={handleConfirm}
      >
        {options?.confirmText ?? 'Confirm'}
      </Button>
    </>
  )

  return (
    <ConfirmContext.Provider value={{ confirm }}>
      {children}
      <Modal
        open={open}
        onClose={handleCancel}
        title={options?.title ?? 'Confirm Action'}
        footer={footer}
      >
        <p className="text-sm text-text-mute leading-relaxed">
          {options?.message}
        </p>
      </Modal>
    </ConfirmContext.Provider>
  )
}
