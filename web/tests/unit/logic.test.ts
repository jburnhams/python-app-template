import { readFileSync } from 'node:fs'
import { colorSchemeScript, format } from 'strata-react'
import { describe, expect, it } from 'vitest'
import { greetingProblem } from '../../src/api'
import { initialMessages, makeMessages, systemNearlyFull, systemStatus } from '../../src/mocks/fixtures'
import { messagePage } from '../../src/mocks/handlers'
import { describeLatest, favouriteWord } from '../../src/screens/GreetingsScreen'
import { describeDisk, homeDisk, ofSize } from '../../src/screens/SystemScreen'

describe('api helpers', () => {
  it("says what is wrong with a name or greeting that is too long, in the server's words, and nothing otherwise", () => {
    expect(greetingProblem('name', 'Ada')).toBeUndefined()
    expect(greetingProblem('name', `  ${'x'.repeat(120)}  `)).toBeUndefined()
    expect(greetingProblem('name', 'x'.repeat(121))).toBe('Use at most 120 characters for the name; this is 121.')
    expect(greetingProblem('greeting', 'g'.repeat(61))).toBe('Use at most 60 characters for the greeting; this is 61.')
  })
})

describe('the Greetings finding and figures', () => {
  it('counts greetings and people and names the latest', () => {
    const two = [
      { id: 2, name: 'Ada', greeting: 'Hi', message: 'Hi, Ada!', created: '2026-11-09T09:12:00Z' },
      { id: 1, name: 'Ada', greeting: 'Hello', message: 'Hello, Ada!', created: '2026-11-08T09:12:00Z' },
    ]
    expect(describeLatest(two)).toBe(
      `${format.count(2, 'greeting')} to ${format.count(1, 'person', 'people')}. The latest, “Hi, Ada!”, went out on ${format.dateTime('2026-11-09T09:12:00Z')}.`,
    )
    expect(describeLatest([])).toBe('No greetings have gone out yet. Send the first one below.')
  })

  it('finds the most used greeting word', () => {
    expect(favouriteWord(initialMessages)).toEqual({ word: 'Hello', times: 4 })
    expect(favouriteWord([])).toBeUndefined()
  })
})

describe('the System finding', () => {
  it("reads the home folder's disk and names the threshold crossed", () => {
    expect(homeDisk(systemStatus)).toEqual({ size: 512e9, used: 512e9 - 210.4e9, free: 210.4e9 })
    expect(homeDisk({ ...systemStatus, folders: [{ name: 'home', path: '/x', exists: false }] })).toBeUndefined()
    expect(ofSize(301.6e9, 512e9)).toBe(`${format.bytes(301.6e9, 'GB')} of ${format.bytes(512e9, 'GB')}`)
    expect(describeDisk(systemStatus)).toBe(`Everything is running. The data disk is 59% full, with ${format.bytes(210.4e9)} free.`)
    expect(describeDisk(systemNearlyFull)).toMatch(/^The data disk is 96% full, .* Free space before greetings stop saving\.$/)
    const filling = { ...systemStatus, folders: [{ name: 'home', path: '/x', exists: true, total_bytes: 100, free_bytes: 15 }] }
    expect(describeDisk(systemStatus, false)).toBe(
      `The server is not answering. When last read, the data disk was 59% full, with ${format.bytes(210.4e9)} free.`,
    )
    expect(describeDisk(filling)).toBe(`The data disk is 85% full, with ${format.bytes(15)} free. Nothing needs doing yet.`)
    const unread = { ...systemStatus, folders: [] }
    expect(describeDisk(unread)).toBe('Everything is running. The data disk could not be read.')
    expect(describeDisk(unread, false)).toBe('The server is not answering.')
  })
})

describe('the mock server', () => {
  it("pages the log after a cursor with the server's own next, as greet.page does", () => {
    const log = makeMessages(5) // ids 5..1, newest first
    const url = (q: string) => `http://x/api/messages/page?${q}`
    expect(messagePage(url('limit=2'), log)).toEqual({ items: log.slice(0, 2), next: '4' })
    expect(messagePage(url('after=2&limit=2'), log)).toEqual({ items: log.slice(4), next: null })
    expect(messagePage(url(''), log).items).toHaveLength(5)
  })
})

describe('index.html', () => {
  it('inlines the colour-scheme script ThemeProvider expects, so a dark page does not flash light', () => {
    const html = readFileSync(new URL('../../index.html', import.meta.url), 'utf8')
    expect(html).toContain(`<script>${colorSchemeScript()}</script>`)
  })
})
