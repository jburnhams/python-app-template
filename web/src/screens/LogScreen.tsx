// The one question: "What went out, and when, all the way back?" A log grows without end, so it
// is read a page at a time, the Strata way: useInfiniteLoad over the server's shared Page shape
// (strata_python.contracts.Page: `items` and `next`, the server's own cursor, never an offset, so a
// greeting removed between pages cannot make the next page skip one; `apiPage` reads both) -> InfiniteList, which loads the next page as the end comes near, shows a
// skeleton for it, a Try again row when it fails and a Show more button for the keyboard. Its
// first page's loading, error and empty states are DataView's, so they read like every other read.
import { apiPage, ButtonLink, EmptyState, format, InfiniteList, PageHeader, Skeleton, useInfiniteLoad } from 'strata-react'
import { api, keys, type Sent } from '../api'

/** Greetings per page. Small enough that the first page is quick, large enough to fill a screen. */
export const PAGE_SIZE = 20

function LogRow({ m }: { m: Sent }) {
  return (
    <div className="flex items-baseline gap-4 py-2 type-body-sm">
      <span className="w-40 shrink-0 text-muted-foreground tabular-nums">{format.dateTime(m.created)}</span>
      <span className="min-w-0 flex-1 truncate">{m.message}</span>
      <span className="hidden w-16 shrink-0 text-right text-muted-foreground tabular-nums sm:block">#{m.id}</span>
    </div>
  )
}

/** Mirrors LogRow: the same heights and column widths, so nothing moves when the rows arrive. */
function RowsSkeleton({ rows = 3 }: { rows?: number }) {
  return (
    <div className="grid">
      {Array.from({ length: rows }, (_, i) => (
        <div key={i} className="flex items-center gap-4 py-3">
          <Skeleton className="h-3.5 w-40" />
          <Skeleton className="h-3.5 flex-1" />
          <Skeleton className="hidden h-3.5 w-16 sm:block" />
        </div>
      ))}
    </div>
  )
}

export function LogScreen() {
  const log = useInfiniteLoad({
    queryKey: keys.log,
    // The server always sends `next`, but strata-python 0.2.6's Page leaves it optional in the schema
    // (a field with a default), so the generated type says `next?`; `?? null` says what is sent.
    queryFn: ({ cursor, signal }) =>
      api
        .get('/api/messages/page', { query: { after: cursor === undefined ? null : Number(cursor), limit: PAGE_SIZE }, signal })
        .then(page => ({ ...page, next: page.next ?? null })),
    itemKey: (m: Sent) => String(m.id),
    ...apiPage<Sent>(),
  })

  return (
    <>
      <PageHeader title="Log" scope="Every greeting kept, newest first" />
      <InfiniteList
        state={log}
        label="Greeting log, newest first"
        moreLabel="Show older greetings"
        skeleton={<RowsSkeleton rows={8} />}
        moreSkeleton={<RowsSkeleton />}
        empty={
          <EmptyState
            title="The log is empty"
            action={
              <ButtonLink to="/" variant="default">
                Send a greeting
              </ButtonLink>
            }
          >
            Each greeting you send is logged here with the time it went out.
          </EmptyState>
        }
        end="That is every greeting kept."
        estimateSize={37}
      >
        {m => <LogRow m={m} />}
      </InfiniteList>
    </>
  )
}
