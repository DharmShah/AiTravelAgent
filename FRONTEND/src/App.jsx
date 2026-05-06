import { useEffect, useRef, useState } from "react";
import { MessageBubble } from "./components/MessageBubble";
import { sendTravelQuery } from "./lib/api";

const initialMessages = [
  {
    id: crypto.randomUUID(),
    role: "assistant",
    text: "Ask for flights in natural language. I will compare Ixigo, Goibibo, and MakeMyTrip, apply your budget, and recommend the best timing within the allowed flexibility window.",
  },
];

function RunwayAnimation() {
  return (
    <div className="flex flex-col items-center justify-center gap-6 py-8">
      <div className="relative w-96 h-32 flex items-center justify-center">
        {/* Runway */}
        <div className="absolute bottom-8 w-full h-1 bg-gradient-to-r from-yellow-400 via-yellow-300 to-transparent">
          {/* Dashes */}
          {[...Array(20)].map((_, i) => (
            <div
              key={i}
              className="absolute bottom-0 h-0.5 bg-yellow-300"
              style={{
                width: "20px",
                left: `${i * 5}%`,
              }}
            />
          ))}
        </div>

        {/* Plane takeoff animation */}
        <div className="runway-plane">✈️</div>
      </div>

      <div className="flex flex-col items-center gap-2">
        <p className="text-sm text-gray-300">Searching for best flights...</p>
        <div className="flex gap-1">
          <span
            className="w-2 h-2 bg-cyan-400 rounded-full animate-bounce"
            style={{ animationDelay: "0s" }}
          ></span>
          <span
            className="w-2 h-2 bg-cyan-400 rounded-full animate-bounce"
            style={{ animationDelay: "0.2s" }}
          ></span>
          <span
            className="w-2 h-2 bg-cyan-400 rounded-full animate-bounce"
            style={{ animationDelay: "0.4s" }}
          ></span>
        </div>
      </div>
    </div>
  );
}

function App() {
  const [query, setQuery] = useState("");
  const [messages, setMessages] = useState(initialMessages);
  const [loading, setLoading] = useState(false);
  const messagesEndRef = useRef(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({
      behavior: "smooth",
      block: "end",
    });
  }, [messages, loading]);

  async function handleSubmit(event) {
    event.preventDefault();

    const trimmedQuery = query.trim();
    if (!trimmedQuery || loading) {
      return;
    }

    const userMessage = {
      id: crypto.randomUUID(),
      role: "user",
      text: trimmedQuery,
    };

    setMessages((current) => [...current, userMessage]);
    setQuery("");
    setLoading(true);

    try {
      const response = await sendTravelQuery(trimmedQuery);
      setMessages((current) => [
        ...current,
        {
          id: crypto.randomUUID(),
          role: "assistant",
          text: response.answer,
          comparison: response.comparison,
        },
      ]);
    } catch (error) {
      setMessages((current) => [
        ...current,
        {
          id: crypto.randomUUID(),
          role: "assistant",
          text: error.message,
        },
      ]);
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="h-screen overflow-hidden bg-gradient-to-br from-slate-900 via-blue-900 to-slate-900 flex items-center justify-center p-2 md:p-3">
      {/* Animated background elements */}
      <div className="fixed inset-0 overflow-hidden pointer-events-none">
        <div className="absolute top-20 left-10 w-64 h-64 bg-cyan-400 rounded-full mix-blend-multiply filter blur-3xl opacity-5 animate-blob"></div>
        <div className="absolute top-40 right-10 w-64 h-64 bg-blue-400 rounded-full mix-blend-multiply filter blur-3xl opacity-5 animate-blob animation-delay-2000"></div>
        <div className="absolute bottom-20 left-1/2 w-64 h-64 bg-purple-400 rounded-full mix-blend-multiply filter blur-3xl opacity-5 animate-blob animation-delay-4000"></div>
      </div>

      <div className="relative z-10 w-full max-w-5xl h-full max-h-[100dvh] flex flex-col">
        {/* Header */}
        <div className="text-center mb-2 md:mb-3 shrink-0">
          <h1 className="text-2xl md:text-4xl font-bold text-white mb-0.5 md:mb-1 font-space-grotesk">
            Flight Search
          </h1>
          <p className="text-xs md:text-sm text-gray-300">
            Your smart AI travel companion
          </p>
        </div>

        {/* Chat Container */}
        <div className="bg-slate-800/40 backdrop-blur-xl rounded-3xl border border-white/10 shadow-2xl overflow-hidden flex flex-col flex-1 min-h-0">
          {/* Chat Header */}
          <div className="bg-gradient-to-r from-cyan-500/20 to-blue-500/20 border-b border-white/5 px-4 md:px-6 py-3">
            <div className="flex items-center justify-between">
              <div>
                <h2 className="text-base md:text-lg font-bold text-white">
                  Travel Assistant
                </h2>
                <p className="text-xs md:text-sm text-gray-400">
                  Live comparison from 3 platforms
                </p>
              </div>
              <div className="w-3 h-3 bg-green-400 rounded-full animate-pulse"></div>
            </div>
          </div>

          {/* Chat Messages */}
          <div className="flex-1 min-h-0 overflow-y-auto px-3 md:px-6 py-4 space-y-4 message-scroll">
            {messages.map((message) => (
              <MessageBubble key={message.id} message={message} />
            ))}

            {loading && (
              <div className="flex justify-center">
                <RunwayAnimation />
              </div>
            )}

            <div ref={messagesEndRef} />
          </div>

          {/* Chat Input */}
          <form
            onSubmit={handleSubmit}
            className="border-t border-white/5 bg-slate-900/50 p-3 md:p-4 shrink-0"
          >
            <div className="space-y-3 flex items-center">
              <textarea
                id="travel-query"
                value={query}
                onChange={(event) => setQuery(event.target.value)}
                placeholder="Find flights from Delhi to Mumbai... Budget: 6000... Flexible timing"
                rows="2"
                className="w-[1050px] mr-[50px] px-4 py-3 bg-slate-700/50 border border-cyan-400/30 rounded-xl text-white placeholder-gray-500 focus:outline-none focus:border-cyan-400 focus:ring-2 focus:ring-cyan-400/20 transition resize-none"
              />

              <div className="flex items-center justify-between">
                <button
                  type="submit"
                  disabled={loading}
                  className="px-5 py-2 bg-gradient-to-r from-cyan-500 to-blue-500 hover:from-cyan-600 hover:to-blue-600 disabled:opacity-50 disabled:cursor-not-allowed text-white text-sm font-semibold rounded-lg transition transform hover:scale-105 active:scale-95"
                >
                  {loading ? "Searching..." : "🚀 Search"}
                </button>
              </div>
            </div>
          </form>
        </div>
      </div>
    </main>
  );
}

export default App;
