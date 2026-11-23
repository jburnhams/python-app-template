// Sample data for the mock server (handlers.ts): the same records answer the unit and integration
// tests, every Storybook story and the visual suite's screenshots, so a screen looks the same in
// each. Dates are fixed, so screenshots do not change from day to day.
import type { Sent, Settings, SystemStatus } from '../api'

export const defaultSettings: Settings = { greeting: 'Hello', style: 'excited' }

const people = ['Grace', 'Alan', 'Ada', 'Linus', 'Margaret', 'Edsger', 'Barbara', 'Ken', 'Frances', 'Dennis', 'Radia', 'Tim']
const words = ['Hello', 'Hello', 'Welcome', 'Good morning', 'Hello', 'Hi']

/** `n` greetings, newest first, one every 97 minutes back from 09:12 UTC on 9 November 2026: the shape `GET /api/messages` returns. */
export function makeMessages(n: number): Sent[] {
  const newest = Date.UTC(2026, 10, 9, 9, 12)
  return Array.from({ length: n }, (_, i) => {
    const id = n - i
    const name = people[id % people.length]
    const greeting = words[id % words.length]
    return { id, name, greeting, message: `${greeting}, ${name}!`, created: new Date(newest - i * 97 * 60_000).toISOString() }
  })
}

/** What the server holds in the healthy state: eight greetings. */
export const initialMessages = makeMessages(8)

/** A long log, for paging: 75 greetings, so the Log screen needs four pages of 20. */
export const longLog = makeMessages(75)

export const GB = 1e9

const home = (total: number, free: number) => [{ name: 'home', path: '/home/ada/.app', exists: true, total_bytes: total, free_bytes: free }]

export const systemStatus: SystemStatus = {
  version: '0.1.0',
  commit: '1427b94c0ffee5ea1d2b3c4d5e6f708192a3b4c5',
  python: '3.13.1',
  platform: 'Linux-6.8.0-x86_64-with-glibc2.39',
  started_at: '2026-11-09T08:00:00Z',
  folders: home(512 * GB, 210.4 * GB),
  services: [],
  greetings: initialMessages.length,
  home_bytes: 18_432,
}

/** The same server with its disk past the "nearly full" threshold. */
export const systemNearlyFull: SystemStatus = { ...systemStatus, home_bytes: 2.4 * GB, folders: home(512 * GB, 20 * GB) }
