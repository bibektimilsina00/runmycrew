import { User as UserIcon, Mail, Calendar, Shield, CheckCircle2 } from 'lucide-react'
import {
  Card, Button, Input, FormField, Divider, Avatar, Badge,
} from '@/shared/components'
import type { UserProfile } from '../types/settingsTypes'

interface ProfileCardProps {
  profile: UserProfile
  fullName: string
  onFullNameChange: (value: string) => void
  onSave: () => void
}

export function ProfileCard({ profile, fullName, onFullNameChange, onSave }: ProfileCardProps) {
  return (
    <Card padding="lg" className="flex flex-col gap-4">
      <div className="flex flex-col gap-1 pb-3 border-b border-border-faint">
        <h3 className="text-sm font-semibold text-text tracking-tight flex items-center gap-2">
          <UserIcon size={14} className="text-accent" />
          <span>Profile Information</span>
        </h3>
        <p className="text-xs text-text-faint">Update your identity and contact parameters.</p>
      </div>

      <div className="flex flex-col md:flex-row md:items-center gap-6 py-2">
        <Avatar
          src={profile.avatarUrl}
          fallback={profile.fullName || profile.email || '?'}
          size="lg"
          className="w-16 h-16 bg-accent/15 text-accent border border-border-faint text-lg"
        />
        <div className="flex flex-col gap-1.5">
          <span className="text-xs font-semibold text-text">Workspace Account</span>
          <div className="flex flex-wrap gap-2">
            <Badge variant="accent" className="flex items-center gap-1 text-[10px]">
              <Shield size={10} /> Active Session
            </Badge>
            <Badge variant="ok" className="flex items-center gap-1 text-[10px]">
              <Calendar size={10} /> Created: {profile.createdAt ? new Date(profile.createdAt).toLocaleDateString() : 'N/A'}
            </Badge>
          </div>
        </div>
      </div>

      <Divider />

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <FormField label="Full Name">
          <Input
            type="text"
            value={fullName}
            onChange={(e) => onFullNameChange(e.target.value)}
            placeholder="John Doe"
            leftIcon={<UserIcon />}
          />
        </FormField>

        <FormField label="Email Address">
          <Input
            type="email"
            value={profile.email}
            disabled
            placeholder="name@company.com"
            leftIcon={<Mail />}
          />
        </FormField>
      </div>

      <div className="flex justify-end pt-2">
        <Button variant="primary" onClick={onSave}>
          <CheckCircle2 size={12} className="mr-1.5" />
          Save Profile
        </Button>
      </div>
    </Card>
  )
}
