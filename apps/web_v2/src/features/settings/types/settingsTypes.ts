export interface ApiKey {
  id: string
  name: string
  token: string
  createdAt: string
}

export interface UserProfile {
  fullName: string
  email: string
  avatarUrl?: string
  createdAt?: string
}
