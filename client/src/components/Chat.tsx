import { useState, useRef, useEffect } from "react"
import { Send, Bot, User, Loader2, RotateCcw } from "lucide-react"
import ReactMarkdown from "react-markdown"
import { Button } from "./ui/Button"

interface Message {
  role: "user" | "assistant"
  content: string
  timestamp: Date
}

const SUGGESTIONS = [
  "What is my current USD position?",
  "Book a 5M USD/CAD FX spot at 1.37 with Goldman Sachs",
  "Show my limit utilization for JP Morgan",
  "What are my cashflows for the next 7 days?",
  "Run mark-to-market on my open positions",
  "What is my exposure to Deutsche Bank?",
  "List all pending deals",
  "Get the latest USD/CAD rate",
]

export default function Chat() {
  const [messages, setMessages] = useState<Message[]>([])
  const [input, setInput] = useState("")
  const [loading, setLoading] = useState(false)
  const [sessionId, setSessionId] = useState<string | null>(null)
  const bottomRef = useRef<HTMLDivElement>(null)
  const inputRef = useRef<HTMLTextAreaElement>(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" })
  }, [messages, loading])

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault()
      sendMessage()
    }
  }

  const sendMessage = async (text?: string) => {
    const msg = text || input.trim()
    if (!msg || loading) return

    const userMsg: Message = { role: "user", content: msg, timestamp: new Date() }
    setMessages((prev) => [...prev, userMsg])
    setInput("")
    setLoading(true)

    try {
      const res = await fetch("/api/v1/copilot/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: msg, session_id: sessionId }),
      })
      const data = await res.json()
      setSessionId(data.session_id)
      setMessages((prev) => [...prev, { role: "assistant", content: data.response, timestamp: new Date() }])
    } catch {
      setMessages((prev) => [...prev, { role: "assistant", content: "⚠️ Error connecting to server. Make sure the backend is running on port 8000.", timestamp: new Date() }])
    } finally {
      setLoading(false)
      inputRef.current?.focus()
    }
  }

  const resetChat = () => {
    setMessages([])
    setSessionId(null)
  }

  return (
    <div className="flex flex-col h-screen bg-[#f7f7f8]">
      {/* Header */}
      <header className="bg-white border-b border-gray-200 px-6 py-3 flex items-center justify-between shadow-sm">
        <div className="flex items-center gap-3">
          <div className="bg-gradient-to-br from-blue-600 to-indigo-700 rounded-xl p-2.5">
            <Bot className="w-5 h-5 text-white" />
          </div>
          <div>
            <h1 className="text-base font-semibold text-gray-900">Treasury AI Copilot</h1>
            <p className="text-xs text-gray-500">CIBC Finance • Powered by AI</p>
          </div>
        </div>
        {messages.length > 0 && (
          <Button variant="ghost" size="sm" onClick={resetChat} className="text-gray-500 hover:text-gray-700">
            <RotateCcw className="w-4 h-4 mr-1" /> New Chat
          </Button>
        )}
      </header>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto">
        {messages.length === 0 ? (
          <div className="max-w-3xl mx-auto px-4 pt-16 pb-8">
            <div className="text-center mb-10">
              <div className="bg-gradient-to-br from-blue-600 to-indigo-700 rounded-2xl p-4 w-16 h-16 mx-auto mb-5 flex items-center justify-center">
                <Bot className="w-8 h-8 text-white" />
              </div>
              <h2 className="text-2xl font-semibold text-gray-800 mb-2">How can I help you today?</h2>
              <p className="text-gray-500">I can book trades, check positions, monitor limits, and run valuations.</p>
            </div>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 max-w-2xl mx-auto">
              {SUGGESTIONS.map((s) => (
                <button
                  key={s}
                  onClick={() => sendMessage(s)}
                  className="text-left text-sm px-4 py-3.5 rounded-xl border border-gray-200 bg-white hover:border-blue-300 hover:shadow-sm transition-all text-gray-700 hover:text-gray-900"
                >
                  {s}
                </button>
              ))}
            </div>
          </div>
        ) : (
          <div className="max-w-3xl mx-auto px-4 py-6 space-y-6">
            {messages.map((msg, i) => (
              <div key={i} className={`flex gap-4 ${msg.role === "user" ? "justify-end" : ""}`}>
                {msg.role === "assistant" && (
                  <div className="flex-shrink-0 w-8 h-8 rounded-full bg-gradient-to-br from-blue-600 to-indigo-700 flex items-center justify-center mt-1">
                    <Bot className="w-4 h-4 text-white" />
                  </div>
                )}
                <div className={`max-w-[85%] ${msg.role === "user" ? "order-first" : ""}`}>
                  <div
                    className={`rounded-2xl px-4 py-3 ${
                      msg.role === "user"
                        ? "bg-blue-600 text-white ml-auto"
                        : "bg-white border border-gray-100 shadow-sm text-gray-800"
                    }`}
                  >
                    {msg.role === "assistant" ? (
                      <div className="prose prose-sm max-w-none prose-p:my-1 prose-ul:my-1 prose-li:my-0.5 prose-headings:my-2 prose-pre:bg-gray-900 prose-pre:text-gray-100 prose-code:text-blue-600 prose-code:bg-blue-50 prose-code:px-1 prose-code:rounded">
                        <ReactMarkdown>{msg.content}</ReactMarkdown>
                      </div>
                    ) : (
                      <p className="text-sm whitespace-pre-wrap">{msg.content}</p>
                    )}
                  </div>
                  <p className={`text-[10px] text-gray-400 mt-1 ${msg.role === "user" ? "text-right" : ""}`}>
                    {msg.timestamp.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}
                  </p>
                </div>
                {msg.role === "user" && (
                  <div className="flex-shrink-0 w-8 h-8 rounded-full bg-gray-700 flex items-center justify-center mt-1">
                    <User className="w-4 h-4 text-white" />
                  </div>
                )}
              </div>
            ))}

            {loading && (
              <div className="flex gap-4">
                <div className="flex-shrink-0 w-8 h-8 rounded-full bg-gradient-to-br from-blue-600 to-indigo-700 flex items-center justify-center mt-1">
                  <Loader2 className="w-4 h-4 text-white animate-spin" />
                </div>
                <div className="bg-white border border-gray-100 shadow-sm rounded-2xl px-4 py-3">
                  <div className="flex items-center gap-1">
                    <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce [animation-delay:0ms]"></div>
                    <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce [animation-delay:150ms]"></div>
                    <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce [animation-delay:300ms]"></div>
                  </div>
                </div>
              </div>
            )}
            <div ref={bottomRef} />
          </div>
        )}
      </div>

      {/* Input */}
      <div className="border-t border-gray-200 bg-white px-4 py-4">
        <div className="max-w-3xl mx-auto">
          <div className="flex items-end gap-2 bg-gray-50 border border-gray-200 rounded-2xl px-4 py-2 focus-within:border-blue-400 focus-within:ring-2 focus-within:ring-blue-100 transition-all">
            <textarea
              ref={inputRef}
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Message Treasury Copilot..."
              rows={1}
              className="flex-1 bg-transparent resize-none text-sm py-2 focus:outline-none placeholder-gray-400 max-h-32"
              disabled={loading}
            />
            <Button
              onClick={() => sendMessage()}
              disabled={loading || !input.trim()}
              size="icon"
              className="rounded-xl h-9 w-9 flex-shrink-0"
            >
              <Send className="w-4 h-4" />
            </Button>
          </div>
          <p className="text-[11px] text-gray-400 text-center mt-2">
            Treasury AI Copilot can make mistakes. Verify important information.
          </p>
        </div>
      </div>
    </div>
  )
}
