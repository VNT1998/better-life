import { z } from 'zod'

const envSchema = z.object({
  VITE_API_BASE_URL: z.string().default('/api'),
  VITE_APP_NAME: z.string().default('BetterLife'),
})

const parsed = envSchema.safeParse({
  VITE_API_BASE_URL: import.meta.env.VITE_API_BASE_URL,
  VITE_APP_NAME: import.meta.env.VITE_APP_NAME,
})

if (!parsed.success) {
  console.error('Invalid environment variables:', parsed.error.format())
  throw new Error('Invalid frontend environment variables configuration')
}

export const env = parsed.data
