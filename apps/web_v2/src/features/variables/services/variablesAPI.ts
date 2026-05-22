import type { Variable } from '../types/variablesTypes'

const MOCK_VARIABLES: Variable[] = [
  { id: 1, key: 'STRIPE_SECRET_KEY',     val: 'sk_live_4xKz9mNpQ2wR8sT',     scope: 'Production', updated: '2w ago' },
  { id: 2, key: 'HUBSPOT_API_KEY',        val: 'hs_api_4f8a2b1c9d3e7',         scope: 'Production', updated: '1w ago' },
  { id: 3, key: 'CLEARBIT_API_KEY',       val: 'cb_live_7k2m9nP3wX5',          scope: 'Production', updated: '3d ago' },
  { id: 4, key: 'SLACK_BOT_TOKEN',        val: 'xoxb-12345-67890-abcdef',       scope: 'Shared',     updated: '5d ago' },
  { id: 5, key: 'AIRTABLE_TOKEN',         val: 'pat_9qR7sV2mK4nL',             scope: 'Production', updated: '4d ago' },
  { id: 6, key: 'CHURN_THRESHOLD',        val: '0.72',                          scope: 'Shared',     updated: '1d ago',  plain: true },
  { id: 7, key: 'SUPPORT_EMAIL',          val: 'support@yourco.io',             scope: 'Shared',     updated: '3w ago',  plain: true },
  { id: 8, key: 'MAX_RETRIES',            val: '3',                             scope: 'Shared',     updated: '2w ago',  plain: true },
]

export const variablesAPI = {
  getAll: async (): Promise<Variable[]> => MOCK_VARIABLES,
}
