import React from 'react'
import { Plus, Check, ChevronDown, Shield, Globe } from 'lucide-react'
import { cn } from '@/lib/utils'
import { Spinner } from '@/components/ui'
import AddCredentialModal from '@/features/credentials/AddCredentialModal'
import { useCredentialPicker } from '@/features/workflow-editor/panels/inspector/hooks/use-credential-picker'

interface CredentialPickerProps {
  value: string // credential ID
  onChange: (value: string) => void
  credentialType?: string | string[]
  placeholder?: string
}

export const CredentialPicker: React.FC<CredentialPickerProps> = ({
  value,
  onChange,
  credentialType,
  placeholder = 'Select a credential'
}) => {
  const {
    filteredCredentials,
    selectedCredential,
    isLoading,
    isOpen,
    setIsOpen,
    toggleOpen,
    isModalOpen,
    openModal,
    closeModal
  } = useCredentialPicker(value, credentialType)

  return (
    <div className="relative">
      <div
        onClick={toggleOpen}
        className="w-full bg-surface-editor border border-border rounded-md px-3 h-[36px] flex items-center justify-between cursor-pointer hover:border-border-strong transition-colors"
      >
        <div className="flex items-center gap-2 overflow-hidden">
          {selectedCredential ? (
            <>
              {selectedCredential.type.includes('oauth') ? (
                <Globe size={14} className="text-blue-400 shrink-0" />
              ) : (
                <Shield size={14} className="text-green-400 shrink-0" />
              )}
              <span className="text-[13px] text-white truncate">{selectedCredential.name}</span>
            </>
          ) : (
            <span className="text-[13px] text-text-placeholder">{placeholder}</span>
          )}
        </div>
        <ChevronDown className={cn("w-4 h-4 text-text-placeholder transition-transform", isOpen && "rotate-180")} />
      </div>

      {isOpen && (
        <>
          <div
            className="fixed inset-0 z-[60]"
            onClick={() => setIsOpen(false)}
          />
          <div className="absolute top-full left-0 right-0 mt-1 bg-surface-modal border border-border rounded-md shadow-2xl z-[70] py-1 max-h-[240px] overflow-y-auto custom-scrollbar animate-in fade-in slide-in-from-top-1 duration-200">
            {isLoading ? (
              <div className="px-3 py-4 text-center">
                <Spinner size="sm" color="accent" className="mx-auto" />
              </div>
            ) : filteredCredentials.length === 0 ? (
              <div className="px-3 py-4 text-center">
                <p className="text-[11px] text-text-muted">No credentials found for this service</p>
              </div>
            ) : (
              filteredCredentials.map((cred) => (
                <div
                  key={cred.id}
                  onClick={() => {
                    onChange(cred.id)
                    setIsOpen(false)
                  }}
                  className={cn(
                    "px-3 py-2 flex items-center justify-between cursor-pointer hover:bg-surface-editor transition-colors group",
                    value === cred.id && "bg-surface-editor"
                  )}
                >
                  <div className="flex items-center gap-2 overflow-hidden">
                    {cred.type.includes('oauth') ? (
                      <Globe size={14} className="text-blue-400 shrink-0" />
                    ) : (
                      <Shield size={14} className="text-green-400 shrink-0" />
                    )}
                    <span className={cn(
                      "text-[13px] truncate",
                      value === cred.id ? "text-white font-medium" : "text-[#AAA] group-hover:text-white"
                    )}>
                      {cred.name}
                    </span>
                  </div>
                  {value === cred.id && <Check size={14} className="text-blue-500" />}
                </div>
              ))
            )}
            
            <div className="border-t border-border mt-1 pt-1">
              <button
                onClick={openModal}
                className="w-full px-3 py-2 flex items-center gap-2 text-[12px] font-bold text-blue-500 hover:bg-blue-500/5 transition-colors text-left"
              >
                <Plus size={14} />
                Add New Credential
              </button>
            </div>
          </div>
        </>
      )}

      <AddCredentialModal
        isOpen={isModalOpen}
        onClose={closeModal}
      />
    </div>
  )
}
