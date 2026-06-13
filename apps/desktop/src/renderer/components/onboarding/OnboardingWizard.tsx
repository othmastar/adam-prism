import React, { useState } from 'react'
import { Server, Globe, Key, ArrowLeft, ArrowRight, Check, Wifi, WifiOff, Loader2, Sparkles } from 'lucide-react'
import { Button } from '../ui/Button'
import { useStore } from '../../lib/store'
import { cn } from '../../lib/utils'

const STEPS = [
  { id: 'welcome', title: 'مرحباً بك في آدم بريزم' },
  { id: 'connection', title: 'إعداد الاتصال' },
  { id: 'complete', title: 'جاهز!' }
]

export function OnboardingWizard() {
  const [currentStep, setCurrentStep] = useState(0)
  const [isLocal, setIsLocal] = useState(true)
  const [backendUrl, setBackendUrl] = useState('http://localhost:8000')
  const [apiKey, setApiKey] = useState('')
  const [checking, setChecking] = useState(false)
  const [connected, setConnected] = useState<boolean | null>(null)
  const setOnboardingVisible = useStore((s) => s.setOnboardingVisible)
  const setSettings = useStore((s) => s.setSettings)

  const handleCheck = async () => {
    setChecking(true)
    setConnected(null)
    try {
      await window.api.setSettings({ backendUrl, apiKey, isLocal })
      const result = await window.api.checkBackend()
      setConnected(result.connected)
    } catch {
      setConnected(false)
    } finally {
      setChecking(false)
    }
  }

  const handleComplete = async () => {
    await window.api.completeOnboarding({ backendUrl, apiKey, isLocal })
    setSettings({
      backendUrl,
      apiKey,
      isLocal,
      onboardingComplete: true
    })
    setOnboardingVisible(false)
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-dark-900/95 backdrop-blur-md">
      <div className="w-full max-w-md mx-4 animate-fadeIn">
        {/* Progress */}
        <div className="flex items-center gap-2 mb-8 px-4">
          {STEPS.map((step, i) => (
            <React.Fragment key={step.id}>
              <div
                className={cn(
                  'w-8 h-8 rounded-full flex items-center justify-center text-xs font-medium transition-colors',
                  i < currentStep ? 'bg-accent text-white' :
                  i === currentStep ? 'bg-accent/20 text-accent border-2 border-accent' :
                  'bg-dark-700 text-dark-400'
                )}
              >
                {i < currentStep ? <Check size={14} /> : i + 1}
              </div>
              {i < STEPS.length - 1 && (
                <div className={cn('flex-1 h-0.5 rounded', i < currentStep ? 'bg-accent' : 'bg-dark-700')} />
              )}
            </React.Fragment>
          ))}
        </div>

        {/* Step content */}
        <div className="bg-dark-800 border border-dark-600 rounded-2xl p-8 shadow-2xl">
          {currentStep === 0 && (
            <div className="text-center">
              <div className="w-24 h-24 rounded-3xl bg-gradient-to-br from-accent to-emerald-400 flex items-center justify-center mx-auto mb-6 shadow-lg shadow-accent/20">
                <span className="text-4xl font-bold text-white">A</span>
              </div>
              <h2 className="text-2xl font-bold text-dark-100 mb-3">مرحباً بك في آدم بريزم</h2>
              <p className="text-sm text-dark-400 leading-relaxed mb-6">
                وكيل الذكاء الاصطناعي المتقدم للبرمجة والبحث والمحادثة.
                <br />
                دعنا نعد التطبيق لك في خطوات بسيطة.
              </p>

              <div className="grid grid-cols-3 gap-3 mb-6">
                <div className="bg-dark-700 rounded-xl p-3 text-center">
                  <Sparkles size={20} className="mx-auto text-accent mb-1" />
                  <span className="text-[10px] text-dark-300">ذكاء متقدم</span>
                </div>
                <div className="bg-dark-700 rounded-xl p-3 text-center">
                  <Server size={20} className="mx-auto text-accent mb-1" />
                  <span className="text-[10px] text-dark-300">أدوات متعددة</span>
                </div>
                <div className="bg-dark-700 rounded-xl p-3 text-center">
                  <Globe size={20} className="mx-auto text-accent mb-1" />
                  <span className="text-[10px] text-dark-300">عربي أولاً</span>
                </div>
              </div>

              <Button onClick={() => setCurrentStep(1)} className="w-full">
                ابدأ الإعداد
                <ArrowLeft size={14} />
              </Button>
            </div>
          )}

          {currentStep === 1 && (
            <div>
              <h2 className="text-xl font-bold text-dark-100 mb-4 text-center">إعداد الاتصال</h2>
              <p className="text-sm text-dark-400 mb-6 text-center">
                اختر كيف تريد الاتصال بخادم آدم بريزم
              </p>

              {/* Connection type */}
              <div className="flex gap-3 mb-5">
                <button
                  onClick={() => { setIsLocal(true); setBackendUrl('http://localhost:8000') }}
                  className={cn(
                    'flex-1 p-4 rounded-xl border text-center transition-all',
                    isLocal ? 'border-accent bg-accent/5' : 'border-dark-600 bg-dark-700 hover:border-dark-500'
                  )}
                >
                  <Server size={24} className={cn('mx-auto mb-2', isLocal ? 'text-accent' : 'text-dark-400')} />
                  <div className="text-xs font-medium text-dark-200">محلي</div>
                  <div className="text-[10px] text-dark-500 mt-1">على هذا الجهاز</div>
                </button>
                <button
                  onClick={() => { setIsLocal(false); setBackendUrl('') }}
                  className={cn(
                    'flex-1 p-4 rounded-xl border text-center transition-all',
                    !isLocal ? 'border-accent bg-accent/5' : 'border-dark-600 bg-dark-700 hover:border-dark-500'
                  )}
                >
                  <Globe size={24} className={cn('mx-auto mb-2', !isLocal ? 'text-accent' : 'text-dark-400')} />
                  <div className="text-xs font-medium text-dark-200">عن بُعد</div>
                  <div className="text-[10px] text-dark-500 mt-1">خادم خارجي</div>
                </button>
              </div>

              {/* URL */}
              <div className="mb-4">
                <label className="block text-xs font-medium text-dark-300 mb-1.5">عنوان الخادم</label>
                <input
                  type="text"
                  value={backendUrl}
                  onChange={(e) => setBackendUrl(e.target.value)}
                  placeholder="http://localhost:8000"
                  className="w-full bg-dark-700 border border-dark-500 rounded-lg px-4 py-2.5 text-sm text-dark-100 placeholder:text-dark-500 focus:outline-none focus:border-accent"
                  dir="ltr"
                />
              </div>

              {/* API Key */}
              <div className="mb-5">
                <label className="block text-xs font-medium text-dark-300 mb-1.5">
                  مفتاح API <span className="text-dark-500">(اختياري)</span>
                </label>
                <div className="relative">
                  <Key size={14} className="absolute right-3 top-1/2 -translate-y-1/2 text-dark-400" />
                  <input
                    type="password"
                    value={apiKey}
                    onChange={(e) => setApiKey(e.target.value)}
                    placeholder="أدخل مفتاح API"
                    className="w-full bg-dark-700 border border-dark-500 rounded-lg px-4 py-2.5 pr-10 text-sm text-dark-100 placeholder:text-dark-500 focus:outline-none focus:border-accent"
                    dir="ltr"
                  />
                </div>
              </div>

              {/* Check connection */}
              <div className="flex items-center gap-3 mb-5">
                <Button onClick={handleCheck} loading={checking} variant="secondary" size="sm">
                  فحص الاتصال
                </Button>
                {connected === true && (
                  <span className="flex items-center gap-1 text-xs text-accent">
                    <Wifi size={14} /> متصل بنجاح
                  </span>
                )}
                {connected === false && (
                  <span className="flex items-center gap-1 text-xs text-danger">
                    <WifiOff size={14} /> فشل الاتصال
                  </span>
                )}
              </div>

              {/* Navigation */}
              <div className="flex gap-3">
                <Button variant="secondary" onClick={() => setCurrentStep(0)} className="flex-1">
                  <ArrowRight size={14} />
                  رجوع
                </Button>
                <Button onClick={() => setCurrentStep(2)} className="flex-1">
                  التالي
                  <ArrowLeft size={14} />
                </Button>
              </div>
            </div>
          )}

          {currentStep === 2 && (
            <div className="text-center">
              <div className="w-16 h-16 rounded-2xl bg-accent/10 flex items-center justify-center mx-auto mb-4">
                <Check size={32} className="text-accent" />
              </div>
              <h2 className="text-xl font-bold text-dark-100 mb-3">أنت جاهز!</h2>
              <p className="text-sm text-dark-400 mb-6">
                تم إعداد آدم بريزم بنجاح. يمكنك الآن البدء في المحادثة.
              </p>

              <div className="bg-dark-700 rounded-xl p-4 mb-6 text-right">
                <div className="space-y-2 text-xs">
                  <div className="flex justify-between">
                    <span className="text-dark-400">نوع الاتصال</span>
                    <span className="text-dark-200">{isLocal ? 'محلي' : 'عن بُعد'}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-dark-400">العنوان</span>
                    <span className="text-dark-200" dir="ltr">{backendUrl}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-dark-400">الحالة</span>
                    <span className={connected ? 'text-accent' : 'text-warning'}>
                      {connected ? 'متصل' : 'سيتم الاتصال لاحقاً'}
                    </span>
                  </div>
                </div>
              </div>

              <div className="flex gap-3">
                <Button variant="secondary" onClick={() => setCurrentStep(1)} className="flex-1">
                  <ArrowRight size={14} />
                  رجوع
                </Button>
                <Button onClick={handleComplete} className="flex-1">
                  ابدأ الآن
                  <Sparkles size={14} />
                </Button>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
