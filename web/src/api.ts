// The server's endpoints, typed from the server itself. `./app openapi` writes web/openapi.json from the
// FastAPI routes, and `npm run api-types` (strata-react's strata-api-types) turns it into
// api.generated.ts, which is committed and never edited: a route or model change on the Python side
// shows up here as a type error, and CI fails a stale file on both sides (`app openapi --check`,
// `npm run api-types:check`).
//
// Reads go through useLoad / useInfiniteLoad and writes through useAsyncAction; both call `api`, a
// createTypedApi over the generated paths, so the path, its {params}, the query, the JSON body and the
// answer are all checked. It puts the app's base before every path (the server gives every page a
// relative <base> back to its root, so the app works behind a reverse proxy at /<prefix>/), and a
// non-2xx answer throws HttpError with the server's own sentence (`detail`) as its `reason`.
import { createTypedApi } from 'strata-react'
import type { paths, Schema } from './api.generated'

export type Settings = Schema<'AppSettings'>
export type Style = Settings['style']
export type Greeting = Schema<'Greeting'>
export type Sent = Schema<'Sent'>
export type SentPage = Schema<'Page_Sent_'>
export type Folder = Schema<'Folder'>
/** `GET /api/system`: strata-python's SystemInfo plus this app's own numbers (src/app/system.py
 *  AppNumbers). Those are extra fields on the shared model, so the schema does not name them. */
export type SystemStatus = Schema<'SystemInfo'> & { greetings: number; home_bytes: number }

export const api = createTypedApi<paths>()

/** The query keys the screens share, so a write can invalidate every read it changes. */
export const keys = {
  system: ['system'],
  settings: ['settings'],
  messages: ['messages'],
  log: ['messages', 'log'],
} as const

/** The styles in the order the settings form offers them, each with what it does. */
export const styles: { value: Style; label: string; example: string }[] = [
  { value: 'excited', label: 'Excited', example: 'Hello, Ada!' },
  { value: 'calm', label: 'Calm', example: 'Hello, Ada.' },
]

/** The server's own limits (src/app/greet.py), checked here too so a person sees the reason before
 *  sending. The server refuses with the same sentence, which reaches the field as the error's reason. */
export const limits = { name: 120, greeting: 60 } as const

/** What is wrong with a greeting's name or word, in the server's words, or undefined when it can be sent. */
export function greetingProblem(field: 'name' | 'greeting', value: string): string | undefined {
  const max = limits[field]
  const length = value.trim().length
  return length > max ? `Use at most ${max} characters for the ${field}; this is ${length}.` : undefined
}
