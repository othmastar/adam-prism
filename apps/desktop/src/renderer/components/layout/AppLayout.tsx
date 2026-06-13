import React from 'react'
import { TitleBar } from './TitleBar'
import { Sidebar } from './Sidebar'
import { PanelLayout } from './PanelLayout'
import { ChatInterface } from '../chat/ChatInterface'
import { CommandPalette } from '../ui/CommandPalette'
import { SettingsModal } from '../settings/SettingsModal'
import { OnboardingWizard } from '../onboarding/OnboardingWizard'
import { useStore } from '../../lib/store'

export function AppLayout() {
  const onboardingVisible = useStore((s) => s.onboardingVisible)
  const settingsOpen = useStore((s) => s.settingsOpen)

  return (
    <div className="h-screen w-screen flex flex-col bg-dark-900 text-dark-100 overflow-hidden" dir="rtl">
      <TitleBar />
      <div className="flex-1 flex overflow-hidden">
        <Sidebar />
        <PanelLayout>
          <ChatInterface />
        </PanelLayout>
      </div>

      {/* Overlays */}
      <CommandPalette />
      {settingsOpen && <SettingsModal />}
      {onboardingVisible && <OnboardingWizard />}
    </div>
  )
}
