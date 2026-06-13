import { z } from 'zod'
import { requestJson } from '@/shared/utils/apiClient'
import { API_ROUTES } from '@/shared/constants/routes'
import {
  SkillMetaSchema,
  SkillSchema,
  type Skill,
  type SkillCreate,
  type SkillMeta,
  type SkillUpdate,
} from '../types/skillTypes'

const SkillMetaListSchema = z.array(SkillMetaSchema)

export const skillsAPI = {
  list: (signal?: AbortSignal): Promise<SkillMeta[]> =>
    requestJson(SkillMetaListSchema, {
      url: API_ROUTES.SKILLS_LIST,
      method: 'GET',
      signal,
    }),

  get: (id: string, signal?: AbortSignal): Promise<Skill> =>
    requestJson(SkillSchema, {
      url: API_ROUTES.SKILL(id),
      method: 'GET',
      signal,
    }),

  create: (data: SkillCreate): Promise<Skill> =>
    requestJson(SkillSchema, {
      url: API_ROUTES.SKILL_CREATE,
      method: 'POST',
      data,
    }),

  update: (id: string, data: SkillUpdate): Promise<Skill> =>
    requestJson(SkillSchema, {
      url: API_ROUTES.SKILL(id),
      method: 'PUT',
      data,
    }),

  delete: (id: string): Promise<void> =>
    requestJson(z.unknown(), {
      url: API_ROUTES.SKILL(id),
      method: 'DELETE',
    }).then(() => undefined),
}
