import { useState, useCallback } from 'react'
import { useNavigate } from 'react-router-dom'
import { Plus, X, Loader2, Sparkles, Check, AlertCircle } from 'lucide-react'
import clsx from 'clsx'
import { useCreateAgent } from '@/hooks/useAgentCatalog'
import type { AgentCategory, SeniorityLevel, CreateAgentPayload } from '@/types'

const CATEGORIES: { value: AgentCategory; label: string }[] = [
  { value: 'dev', label: 'Development' },
  { value: 'ops', label: 'Operations' },
  { value: 'qa', label: 'Quality Assurance' },
  { value: 'ai', label: 'AI / ML' },
  { value: 'data', label: 'Data Engineering' },
  { value: 'general', label: 'General' },
]

const SENIORITY_LEVELS: SeniorityLevel[] = ['junior', 'mid', 'senior', 'staff', 'lead']

const POPULAR_EMOJIS = ['🤖', '🧑‍💻', '⚙️', '🔧', '🧪', '📊', '🧠', '🚀', '🛡️', '🌐', '🔮', '🎯']

interface FormState {
  name: string
  category: AgentCategory
  emoji: string
  description: string
  stack_keywords: string[]
  seniority_levels: SeniorityLevel[]
  tools_json: string
}

const DEFAULT_FORM: FormState = {
  name: '',
  category: 'dev',
  emoji: '🤖',
  description: '',
  stack_keywords: [],
  seniority_levels: ['junior', 'mid', 'senior'],
  tools_json: '[]',
}

export function AgentBuilder() {
  const navigate = useNavigate()
  const createAgent = useCreateAgent()

  const [form, setForm] = useState<FormState>(DEFAULT_FORM)
  const [keywordInput, setKeywordInput] = useState('')
  const [showEmojiPicker, setShowEmojiPicker] = useState(false)
  const [generatedPrompt, setGeneratedPrompt] = useState<string | null>(null)
  const [saved, setSaved] = useState(false)
  const [error, setError] = useState('')

  const updateForm = useCallback(<K extends keyof FormState>(key: K, value: FormState[K]) => {
    setForm((prev) => ({ ...prev, [key]: value }))
  }, [])

  const addKeyword = () => {
    const kw = keywordInput.trim()
    if (kw && !form.stack_keywords.includes(kw)) {
      updateForm('stack_keywords', [...form.stack_keywords, kw])
    }
    setKeywordInput('')
  }

  const removeKeyword = (kw: string) => {
    updateForm('stack_keywords', form.stack_keywords.filter((k) => k !== kw))
  }

  const toggleSeniority = (level: SeniorityLevel) => {
    if (form.seniority_levels.includes(level)) {
      updateForm('seniority_levels', form.seniority_levels.filter((l) => l !== level))
    } else {
      updateForm('seniority_levels', [...form.seniority_levels, level])
    }
  }

  const handleGenerate = async () => {
    if (!form.name.trim()) {
      setError('The agent name is required')
      return
    }
    setError('')

    let tools: unknown[] = []
    try {
      tools = JSON.parse(form.tools_json) as unknown[]
    } catch {
      setError('The tools JSON is not valid')
      return
    }

    const payload: CreateAgentPayload = {
      name: form.name,
      category: form.category,
      icon: form.emoji,
      stack_keywords: form.stack_keywords,
      seniority_levels: form.seniority_levels,
      tools: tools as unknown as Record<string, string[]>,
    }

    try {
      const agent = await createAgent.mutateAsync(payload)
      setGeneratedPrompt(agent.system_prompt_template ?? `You are ${agent.name}, an onboarding agent specialized in ${agent.category}. Your goal is to guide new developers during their first 14 days.`)
      setSaved(false)
    } catch (err) {
      const msg = err instanceof Error ? err.message : 'Error creating the agent'
      setError(msg)
      // For demo, show a generated prompt anyway
      setGeneratedPrompt(
        `You are ${form.name}, an onboarding agent specialized in ${form.category}.\n\n` +
        `Your technology stack includes: ${form.stack_keywords.join(', ') || 'modern technologies'}.\n\n` +
        `You conduct welcome interviews with ${form.seniority_levels.join(', ')} level developers, ` +
        `identify their strengths and areas for improvement, and generate personalized 14-day onboarding plans.\n\n` +
        `You are friendly, technical, and direct. You ask precise questions about previous experience, work preferences, and career goals.`
      )
    }
  }

  const handleSave = () => {
    setSaved(true)
    setTimeout(() => navigate('/agents'), 1200)
  }

  const isFormValid =
    form.name.trim() !== '' && form.seniority_levels.length > 0

  return (
    <div className="p-6 max-w-7xl mx-auto">
      {/* Header */}
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-white">Create Custom Agent</h1>
        <p className="text-gray-500 text-sm mt-1">
          Define a specialized agent and generate its system prompt with Gemini
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* LEFT PANEL: Form */}
        <div className="space-y-5">
          {/* Emoji + Name */}
          <div className="bg-gray-900 border border-gray-800 rounded-xl p-5 space-y-4">
            <h2 className="text-xs font-semibold text-gray-500 uppercase tracking-wider">Identity</h2>

            {/* Emoji Picker */}
            <div>
              <label className="text-xs text-gray-500 block mb-2">Icon</label>
              <div className="relative">
                <button
                  onClick={() => setShowEmojiPicker(!showEmojiPicker)}
                  className="w-14 h-14 rounded-xl bg-gray-800 border border-gray-700 hover:border-indigo-500 transition-colors text-3xl flex items-center justify-center"
                >
                  {form.emoji}
                </button>
                {showEmojiPicker && (
                  <div className="absolute top-16 left-0 z-10 bg-gray-800 border border-gray-700 rounded-xl p-3 flex flex-wrap gap-2 w-64 shadow-xl">
                    {POPULAR_EMOJIS.map((e) => (
                      <button
                        key={e}
                        onClick={() => {
                          updateForm('emoji', e)
                          setShowEmojiPicker(false)
                        }}
                        className="w-10 h-10 rounded-lg hover:bg-gray-700 text-2xl flex items-center justify-center transition-colors"
                      >
                        {e}
                      </button>
                    ))}
                  </div>
                )}
              </div>
            </div>

            {/* Name */}
            <div>
              <label className="text-xs text-gray-500 block mb-1.5">Agent Name</label>
              <input
                type="text"
                value={form.name}
                onChange={(e) => updateForm('name', e.target.value)}
                placeholder="e.g. Alex Backend Pro"
                className="w-full px-3 py-2.5 bg-gray-800 border border-gray-700 rounded-lg text-sm text-gray-200 focus:outline-none focus:border-indigo-500 transition-colors placeholder:text-gray-600"
              />
            </div>

            {/* Category */}
            <div>
              <label className="text-xs text-gray-500 block mb-1.5">Category</label>
              <select
                value={form.category}
                onChange={(e) => updateForm('category', e.target.value as AgentCategory)}
                className="w-full px-3 py-2.5 bg-gray-800 border border-gray-700 rounded-lg text-sm text-gray-200 focus:outline-none focus:border-indigo-500 transition-colors"
              >
                {CATEGORIES.map((c) => (
                  <option key={c.value} value={c.value}>
                    {c.label}
                  </option>
                ))}
              </select>
            </div>

            {/* Description */}
            <div>
              <label className="text-xs text-gray-500 block mb-1.5">Description</label>
              <textarea
                value={form.description}
                onChange={(e) => updateForm('description', e.target.value)}
                placeholder="Describe the agent's role and specialty..."
                rows={3}
                className="w-full px-3 py-2.5 bg-gray-800 border border-gray-700 rounded-lg text-sm text-gray-200 focus:outline-none focus:border-indigo-500 transition-colors placeholder:text-gray-600 resize-none"
              />
            </div>
          </div>

          {/* Stack Keywords */}
          <div className="bg-gray-900 border border-gray-800 rounded-xl p-5 space-y-3">
            <h2 className="text-xs font-semibold text-gray-500 uppercase tracking-wider">Technology Stack</h2>
            <div className="flex gap-2">
              <input
                type="text"
                value={keywordInput}
                onChange={(e) => setKeywordInput(e.target.value)}
                onKeyDown={(e) => { if (e.key === 'Enter') { e.preventDefault(); addKeyword() } }}
                placeholder="React, Node.js, PostgreSQL..."
                className="flex-1 px-3 py-2 bg-gray-800 border border-gray-700 rounded-lg text-sm text-gray-200 focus:outline-none focus:border-indigo-500 transition-colors placeholder:text-gray-600"
              />
              <button
                onClick={addKeyword}
                className="p-2 rounded-lg bg-indigo-600/20 hover:bg-indigo-600/40 text-indigo-400 border border-indigo-500/30 transition-colors"
              >
                <Plus size={16} />
              </button>
            </div>
            <div className="flex flex-wrap gap-2">
              {form.stack_keywords.map((kw) => (
                <span
                  key={kw}
                  className="flex items-center gap-1.5 px-2.5 py-1 rounded-lg bg-gray-800 text-gray-300 text-xs border border-gray-700"
                >
                  {kw}
                  <button
                    onClick={() => removeKeyword(kw)}
                    className="text-gray-600 hover:text-gray-400 transition-colors"
                  >
                    <X size={12} />
                  </button>
                </span>
              ))}
              {form.stack_keywords.length === 0 && (
                <span className="text-xs text-gray-700">Add stack technologies...</span>
              )}
            </div>
          </div>

          {/* Seniority Levels */}
          <div className="bg-gray-900 border border-gray-800 rounded-xl p-5 space-y-3">
            <h2 className="text-xs font-semibold text-gray-500 uppercase tracking-wider">Seniority Levels</h2>
            <div className="flex flex-wrap gap-2">
              {SENIORITY_LEVELS.map((level) => (
                <button
                  key={level}
                  onClick={() => toggleSeniority(level)}
                  className={clsx(
                    'px-3 py-1.5 rounded-lg text-xs font-medium border transition-all',
                    form.seniority_levels.includes(level)
                      ? 'bg-indigo-600/20 text-indigo-300 border-indigo-500/40'
                      : 'bg-gray-800 text-gray-500 border-gray-700 hover:border-gray-600'
                  )}
                >
                  {level}
                </button>
              ))}
            </div>
          </div>

          {/* Tools JSON */}
          <div className="bg-gray-900 border border-gray-800 rounded-xl p-5 space-y-3">
            <h2 className="text-xs font-semibold text-gray-500 uppercase tracking-wider">Tools (JSON)</h2>
            <textarea
              value={form.tools_json}
              onChange={(e) => updateForm('tools_json', e.target.value)}
              rows={6}
              className="w-full px-3 py-2.5 bg-gray-800 border border-gray-700 rounded-lg text-xs text-gray-300 font-mono focus:outline-none focus:border-indigo-500 transition-colors resize-none"
              placeholder='[{"name": "create_ticket", "description": "..."}]'
            />
          </div>

          {/* Error */}
          {error && (
            <div className="flex items-center gap-2 p-3 rounded-lg bg-red-500/10 border border-red-500/30 text-red-400 text-sm">
              <AlertCircle size={16} />
              <span>{error}</span>
            </div>
          )}

          {/* Generate Button */}
          <button
            onClick={() => void handleGenerate()}
            disabled={!isFormValid || createAgent.isPending}
            className={clsx(
              'w-full py-3 rounded-xl text-sm font-medium flex items-center justify-center gap-2 transition-all',
              isFormValid && !createAgent.isPending
                ? 'bg-indigo-600 hover:bg-indigo-500 text-white'
                : 'bg-gray-800 text-gray-600 cursor-not-allowed'
            )}
          >
            {createAgent.isPending ? (
              <Loader2 size={16} className="animate-spin" />
            ) : (
              <Sparkles size={16} />
            )}
            {createAgent.isPending ? 'Generating with Gemini...' : 'Generate with Gemini'}
          </button>
        </div>

        {/* RIGHT PANEL: Preview */}
        <div className="space-y-5">
          {/* Agent Preview Card */}
          <div className="bg-gray-900 border border-gray-800 rounded-xl p-5">
            <h2 className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-4">Agent Preview</h2>
            <div className="bg-gray-950 border border-gray-800 rounded-xl p-5">
              <div className="flex items-start justify-between mb-4">
                <div className="text-4xl">{form.emoji || '🤖'}</div>
                <span className="text-xs text-gray-600 uppercase tracking-wider">{form.category}</span>
              </div>
              <h3 className="text-lg font-semibold text-white mb-2">
                {form.name || 'Agent name'}
              </h3>
              <p className="text-sm text-gray-500 mb-4 min-h-10">
                {form.description || 'The agent description will appear here...'}
              </p>
              <div className="flex flex-wrap gap-1.5 mb-3">
                {form.seniority_levels.map((level) => (
                  <span
                    key={level}
                    className="px-2 py-0.5 rounded-full text-xs font-medium bg-indigo-500/15 text-indigo-300 border border-indigo-500/25"
                  >
                    {level}
                  </span>
                ))}
              </div>
              <div className="flex flex-wrap gap-1">
                {form.stack_keywords.slice(0, 4).map((kw) => (
                  <span
                    key={kw}
                    className="px-2 py-0.5 rounded-md text-xs bg-gray-800 text-gray-400 border border-gray-700/50"
                  >
                    {kw}
                  </span>
                ))}
              </div>
            </div>
          </div>

          {/* Generated System Prompt */}
          {generatedPrompt && (
            <div className="bg-gray-900 border border-emerald-500/20 rounded-xl p-5 space-y-3">
              <div className="flex items-center gap-2">
                <Sparkles size={14} className="text-emerald-400" />
                <h2 className="text-xs font-semibold text-emerald-400 uppercase tracking-wider">
                  Generated System Prompt
                </h2>
              </div>
              <pre className="text-xs text-gray-300 font-mono whitespace-pre-wrap leading-relaxed bg-gray-950 border border-gray-800 rounded-lg p-4 max-h-64 overflow-y-auto">
                {generatedPrompt}
              </pre>
              <button
                onClick={handleSave}
                disabled={saved}
                className={clsx(
                  'w-full py-2.5 rounded-xl text-sm font-medium flex items-center justify-center gap-2 transition-all',
                  saved
                    ? 'bg-emerald-600/20 text-emerald-400 border border-emerald-500/30'
                    : 'bg-emerald-600 hover:bg-emerald-500 text-white'
                )}
              >
                {saved ? (
                  <>
                    <Check size={16} />
                    Saved — redirecting...
                  </>
                ) : (
                  'Save Agent'
                )}
              </button>
            </div>
          )}

          {/* Empty state */}
          {!generatedPrompt && (
            <div className="bg-gray-900/50 border border-dashed border-gray-800 rounded-xl p-10 text-center">
              <Sparkles size={32} className="text-gray-700 mx-auto mb-3" />
              <p className="text-sm text-gray-600">
                The system prompt generated by Gemini will appear here after clicking{' '}
                <span className="text-gray-500">Generate</span>
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
