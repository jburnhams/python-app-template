// The one question: "Is the app healthy, and will its disk hold?" The read is strata-python's
// shared GET /api/system (every strata app answers it alike: version, commit, start time, each
// folder with its disk) plus this app's own numbers. The finding answers with the home disk's state, from the same thresholds the meter draws; then the next questions in order:
// how full is the disk and what is it full of (a Meter with named thresholds, a CompositionBar
// with its table), what is running (Status words, never colour alone), and where to go next
// (LinkCards). The read is polled; a poll that fails keeps the last readings on screen and says
// how old they are (DataView's stale notice), so a restarting server does not blank the page.
import type { ReactNode } from 'react'
import {
  CompositionBar,
  crossedThreshold,
  DataView,
  EmptyState,
  format,
  LinkCard,
  LinkCardList,
  Meter,
  type MeterThreshold,
  PageHeader,
  Skeleton,
  StaleNotice,
  Status,
  useLoad,
} from 'strata-react'
import { api, type Folder, keys, type SystemStatus } from '../api'

/** One set of thresholds for the data disk, as shares of its size, named in the app's words. */
export const diskThresholds: MeterThreshold[] = [
  { at: 0.8, tone: 'warning', label: 'Filling up' },
  { at: 0.95, tone: 'danger', label: 'Nearly full' },
]

/** "301.6 GB of 512 GB": both in the larger figure's unit, so they read as one comparison. */
export function ofSize(used: number, size: number) {
  const unit = format.byteUnit(size)
  return `${format.bytes(used, unit)} of ${format.bytes(size, unit)}`
}

/** The disk a folder is on, in bytes: its size and what is used of it. */
export type Disk = { size: number; used: number; free: number }

/** The home folder's disk (where the settings and the SQLite database live), or undefined when the
 *  server could not read it (the folder is not made yet and nothing above it exists). */
export function homeDisk(s: SystemStatus): Disk | undefined {
  const home = s.folders?.find((f: Folder) => f.name === 'home')
  if (home?.total_bytes == null || home.free_bytes == null) return undefined
  return { size: home.total_bytes, used: home.total_bytes - home.free_bytes, free: home.free_bytes }
}

/** The page's finding, from the disk the home folder is on. When the latest poll failed, it says so first and reads the disk as old news. */
export function describeDisk(s: SystemStatus, answering = true): string {
  const disk = homeDisk(s)
  if (!disk) return answering ? 'Everything is running. The data disk could not be read.' : 'The server is not answering.'
  const share = disk.used / disk.size
  const crossed = crossedThreshold(share, diskThresholds)
  const left = `${format.bytes(disk.free)} free`
  if (!answering) return `The server is not answering. When last read, the data disk was ${format.percent(share)} full, with ${left}.`
  if (!crossed) return `Everything is running. The data disk is ${format.percent(share)} full, with ${left}.`
  return crossed.tone === 'danger'
    ? `The data disk is ${format.percent(share)} full, with ${left}. Free space before greetings stop saving.`
    : `The data disk is ${format.percent(share)} full, with ${left}. Nothing needs doing yet.`
}

/** One row of the Running list: a term and what it is now. */
function Fact({ term, children }: { term: string; children: ReactNode }) {
  return (
    <div className="flex gap-6">
      <dt className="w-28 shrink-0 text-muted-foreground">{term}</dt>
      <dd>{children}</dd>
    </div>
  )
}

function SystemSkeleton() {
  return (
    <div className="grid gap-10" aria-hidden>
      <Skeleton className="h-16 w-full" />
      <Skeleton className="h-24 w-full max-w-xl" />
      <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-3">
        {[0, 1, 2].map(i => (
          <Skeleton key={i} className="h-28" />
        ))}
      </div>
    </div>
  )
}

export function SystemScreen() {
  const load = useLoad({ queryKey: keys.system, queryFn: () => api.get('/api/system') as Promise<SystemStatus>, refetchInterval: 60_000 })
  // Readings kept from an earlier poll are still shown, but the server is not answering now.
  const answering = !(load.status === 'ready' && load.stale)

  return (
    <>
      <PageHeader
        title="System"
        scope="This computer, checked every minute"
        finding={load.status === 'ready' ? { text: describeDisk(load.data, answering) } : undefined}
      />
      <DataView
        state={load}
        isEmpty={() => false}
        skeleton={<SystemSkeleton />}
        staleNotice={stale => <StaleNotice stale={stale} shown={when => `These readings are from ${when}.`} />}
        empty={<EmptyState title="No readings">The server sent nothing to report.</EmptyState>}
      >
        {s => {
          const disk = homeDisk(s)
          const home = s.folders?.find(f => f.name === 'home')
          return (
            <div className="grid gap-10">
              <section aria-labelledby="disk" className="grid max-w-xl gap-3">
                <h2 id="disk" className="type-heading">
                  Data disk
                </h2>
                <p className="type-body-sm text-muted-foreground">
                  The app’s settings and database are in <span className="font-mono text-foreground">{home?.path ?? format.missing}</span>,
                  on this disk.
                </p>
                {disk ? (
                  <>
                    <Meter
                      label="Data disk space used"
                      value={disk.used}
                      max={disk.size}
                      thresholds={diskThresholds}
                      detail={ofSize(disk.used, disk.size)}
                    />
                    <CompositionBar
                      label={`${format.bytes(disk.size)} in all`}
                      parts={[
                        { key: 'app', label: 'This app’s data', value: s.home_bytes },
                        { key: 'other', label: 'Everything else', value: Math.max(0, disk.used - s.home_bytes) },
                      ]}
                      total={disk.size}
                      restLabel="Free"
                      formatValue={v => format.bytes(v)}
                    />
                  </>
                ) : (
                  <p className="type-body-sm">The disk could not be read.</p>
                )}
              </section>

              <section aria-labelledby="running" className="grid gap-3">
                <h2 id="running" className="type-heading">
                  Running
                </h2>
                <dl className="grid max-w-xl gap-2 type-body-sm">
                  <Fact term="Server">
                    {answering ? <Status tone="success">Answering</Status> : <Status tone="danger">Not answering</Status>}
                    <span className="ml-2 tabular-nums">version {s.version}</span>
                  </Fact>
                  <Fact term="Started">{format.dateTime(s.started_at)}</Fact>
                  <Fact term="Source">
                    <span className="font-mono">{s.commit ? s.commit.slice(0, 12) : 'Installed package'}</span>
                  </Fact>
                  <Fact term="Python">
                    <span className="tabular-nums">{s.python}</span>
                  </Fact>
                  <Fact term="Platform">{s.platform}</Fact>
                  <Fact term="Greetings kept">
                    <span className="tabular-nums">{format.integer(s.greetings)}</span>
                  </Fact>
                </dl>
              </section>

              <section aria-labelledby="next" className="grid gap-3">
                <h2 id="next" className="type-heading">
                  Go to
                </h2>
                <LinkCardList label="Places to go from here">
                  <LinkCard
                    to="/settings"
                    title="Settings"
                    description="Change the default greeting and how greetings end, or choose light or dark."
                  />
                  <LinkCard
                    href={api.url('/api/docs')}
                    title="API reference"
                    description="Every endpoint the server answers, with a form to try each one."
                  />
                  <LinkCard
                    href={api.url('/api/health')}
                    title="Health check"
                    description="The JSON a monitor polls to see that the server is up."
                  />
                </LinkCardList>
              </section>
            </div>
          )
        }}
      </DataView>
    </>
  )
}
