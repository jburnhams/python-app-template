import { HttpResponse, http } from 'msw'
import { describe, expect, it } from 'vitest'
import { saveSettingsFails, settingsError } from '../../src/mocks/handlers'
import { openApp, screen, waitFor } from '../utils/render'
import { mock, server } from '../utils/server'

describe('Settings', () => {
  it('starts the form from what the server holds and saves a change', async () => {
    const { user } = openApp('/settings')
    const greeting = await screen.findByRole('textbox', { name: 'Default greeting' })
    expect(greeting).toHaveValue('Hello')
    expect(screen.getByRole('radio', { name: /^Excited/ })).toBeChecked()
    await user.clear(greeting)
    await user.type(greeting, 'Howdy')
    await user.click(screen.getByRole('radio', { name: /^Calm/ }))
    await user.click(screen.getByRole('button', { name: 'Save settings' }))
    expect(await screen.findByText('Saved', { selector: '[role=status]' })).toBeInTheDocument()
    expect(mock.settings).toEqual({ greeting: 'Howdy', style: 'calm' })
  })

  it('says under the field what is wrong, saves nothing, and clears the message as it is fixed', async () => {
    const { user } = openApp('/settings')
    const greeting = await screen.findByRole('textbox', { name: 'Default greeting' })
    await user.clear(greeting)
    await user.click(screen.getByRole('button', { name: 'Save settings' }))
    expect(greeting).toHaveAccessibleDescription(/Enter the word greetings start with/)
    expect(greeting).toBeInvalid()
    expect(mock.settings.greeting).toBe('Hello')
    await user.type(greeting, 'H')
    expect(greeting).not.toBeInvalid()
  })

  it('says why the server refused a change', async () => {
    server.use(
      http.put('*/api/settings', () => HttpResponse.json({ detail: 'greeting: must not be blank', payload: null }, { status: 400 })),
    )
    const { user } = openApp('/settings')
    await user.click(await screen.findByRole('button', { name: 'Save settings' }))
    expect(await screen.findByText(/greeting: must not be blank\.? The settings were not changed\./)).toBeInTheDocument()
  })

  it('says what happened when saving fails', async () => {
    server.use(saveSettingsFails)
    const { user } = openApp('/settings')
    await user.click(await screen.findByRole('button', { name: 'Save settings' }))
    expect(await screen.findByText('The server could not answer (503). The settings were not changed.')).toBeInTheDocument()
  })

  it('keeps the tab in the URL, and the colour scheme choice changes the page', async () => {
    const { user, router } = openApp('/settings')
    await user.click(screen.getByRole('tab', { name: 'Appearance' }))
    expect(router.state.location.search).toBe('?tab=appearance')
    await user.click(screen.getByRole('radio', { name: 'Dark' }))
    await waitFor(() => expect(document.documentElement).toHaveClass('dark'))
  })

  it('opens on a tab from a link', () => {
    openApp('/settings?tab=appearance')
    expect(screen.getByRole('tab', { name: 'Appearance' })).toHaveAttribute('aria-selected', 'true')
    expect(screen.getByRole('radiogroup', { name: 'Colour scheme' })).toBeInTheDocument()
  })

  it('says the server could not answer', async () => {
    server.use(settingsError)
    openApp('/settings')
    expect(await screen.findByRole('alert')).toHaveTextContent('The server could not answer (503)')
  })
})
