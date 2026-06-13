import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { skillsAPI } from '../services/skillsAPI'
import type { SkillCreate, SkillUpdate } from '../types/skillTypes'

const SKILLS_KEY = ['skills'] as const
const skillKey = (id: string) => ['skills', id] as const

/** List every skill in the current workspace (metadata only — no content). */
export function useSkills() {
  return useQuery({
    queryKey: SKILLS_KEY,
    queryFn: ({ signal }) => skillsAPI.list(signal),
    staleTime: 1000 * 60,
  })
}

/** Fetch a single skill with its full content body. */
export function useSkill(id: string | null | undefined) {
  return useQuery({
    queryKey: id ? skillKey(id) : ['skills', 'null'],
    queryFn: ({ signal }) => skillsAPI.get(id as string, signal),
    enabled: Boolean(id),
    staleTime: 1000 * 60,
  })
}

export function useCreateSkill() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (data: SkillCreate) => skillsAPI.create(data),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: SKILLS_KEY })
    },
  })
}

export function useUpdateSkill() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: SkillUpdate }) => skillsAPI.update(id, data),
    onSuccess: (updated) => {
      // Update both the list and the single-skill query without a refetch —
      // the API returns the canonical post-update payload.
      void queryClient.invalidateQueries({ queryKey: SKILLS_KEY })
      queryClient.setQueryData(skillKey(updated.id), updated)
    },
  })
}

export function useDeleteSkill() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (id: string) => skillsAPI.delete(id),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: SKILLS_KEY })
    },
  })
}
