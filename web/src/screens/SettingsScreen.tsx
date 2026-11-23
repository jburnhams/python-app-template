// The one question: "How is the app set up, and how do I change it?" Two tabs whose choice lives
// in the URL (?tab=appearance), so a link can open either one. General is a form over the server's
// settings: the fields start from what the server holds (rendered inside DataView's ready state,
// so they are never blank while loading), problems are said under the field they belong to (the
// action's `validate`), a fixed set of values is a ChoiceGroup typed by the server's enum, and
// saving is one AsyncButton through Saving… and Saved. Appearance is Strata's ColorSchemeChoice,
// which ThemeProvider (main.tsx) keeps in this browser.
import { useQueryClient } from '@tanstack/react-query'
import { type FormEvent, useState } from 'react'
import {
  AsyncButton,
  ChoiceGroup,
  ColorSchemeChoice,
  DataView,
  EmptyState,
  Field,
  Input,
  PageHeader,
  Skeleton,
  Tabs,
  useAsyncAction,
  useLoad,
} from 'strata-react'
import { api, greetingProblem, keys, limits, type Settings, type Style, styles } from '../api'

const tabs = [
  { value: 'general', label: 'General' },
  { value: 'appearance', label: 'Appearance' },
]

export function SettingsScreen() {
  return (
    <>
      <PageHeader title="Settings" scope="Saved on this computer, for every browser that opens the app" />
      <Tabs param="tab" items={tabs} label="Settings">
        {tab => (tab === 'appearance' ? <Appearance /> : <General />)}
      </Tabs>
    </>
  )
}

function General() {
  const load = useLoad({ queryKey: keys.settings, queryFn: () => api.get('/api/settings') })
  return (
    <DataView
      state={load}
      isEmpty={() => false}
      skeleton={<FormSkeleton />}
      empty={<EmptyState title="No settings">The server sent none.</EmptyState>}
    >
      {s => <SettingsForm current={s} />}
    </DataView>
  )
}

/** Mirrors the form: the greeting field with its hint, the two choices, then the button. Heights are
 *  the controls' own (--control-h), so the skeleton follows the app's density. */
function FormSkeleton() {
  return (
    <div className="grid max-w-xl gap-6" aria-hidden>
      <div className="grid gap-1.5">
        <Skeleton className="h-4 w-32" />
        <Skeleton className="h-(--control-h) w-full" />
        <Skeleton className="h-4 w-3/4" />
      </div>
      <div className="grid gap-3">
        <Skeleton className="h-4 w-40" />
        {[0, 1].map(i => (
          <Skeleton key={i} className="h-10 w-2/3" />
        ))}
      </div>
      <Skeleton className="h-(--control-h) w-32" />
    </div>
  )
}

export function SettingsForm({ current }: { current: Settings }) {
  const queryClient = useQueryClient()
  const [greeting, setGreeting] = useState(current.greeting)
  const [style, setStyle] = useState<Style>(current.style)

  const save = useAsyncAction(
    async () => {
      await api.put('/api/settings', { json: { greeting: greeting.trim(), style } })
      // Everything that reads the settings reads again.
      await queryClient.invalidateQueries({ queryKey: keys.settings })
    },
    {
      validate: () => ({
        greeting: greeting.trim() ? greetingProblem('greeting', greeting) : 'Enter the word greetings start with, such as Hello.',
      }),
    },
  )

  const onSubmit = (e: FormEvent) => {
    e.preventDefault()
    void save.run()
  }

  return (
    <form onSubmit={onSubmit} noValidate className="grid max-w-xl gap-6">
      <Field
        label="Default greeting"
        hint={`Used when a greeting is sent without one. Up to ${limits.greeting} characters.`}
        error={save.fieldErrors.greeting}
      >
        <Input
          value={greeting}
          onChange={e => {
            setGreeting(e.target.value)
            save.clearFieldError('greeting')
          }}
          autoComplete="off"
        />
      </Field>
      <ChoiceGroup
        legend="How greetings end"
        name="style"
        value={style}
        onChange={v => setStyle(v as Style)}
        choices={styles.map(s => ({ value: s.value, label: s.label, detail: `“${s.example}”` }))}
      />
      <div className="flex flex-wrap items-center gap-3">
        <AsyncButton
          type="submit"
          variant="default"
          phase={save.phase}
          error={save.error}
          labels={{ idle: 'Save settings', pending: 'Saving…', done: 'Saved' }}
        />
        {save.phase === 'error' && <p className="type-body-sm text-danger">{save.error} The settings were not changed.</p>}
      </div>
    </form>
  )
}

function Appearance() {
  return (
    <div className="grid max-w-xl gap-3">
      <ColorSchemeChoice legend="Colour scheme" />
      <p className="type-body-sm text-muted-foreground">Kept in this browser only.</p>
    </div>
  )
}
