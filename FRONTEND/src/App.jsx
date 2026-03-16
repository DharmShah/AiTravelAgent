import { useState } from "react";
import { MessageBubble } from "./components/MessageBubble";
import { sendTravelQuery } from "./lib/api";

const starterPrompts = [
  "Find flights from Delhi to Mumbai on 20-03-2026 around 5:00 PM under 6000 with flexible timing.",
  "Compare Bangalore to Goa flights for tomorrow morning, budget 7500.",
  "I need an evening flight from Hyderabad to Pune this Friday, cheapest option preferred.",
];

const initialMessages = [
  {
    id: crypto.randomUUID(),
    role: "assistant",
    text: "Ask for flights in natural language. I will compare Ixigo, Goibibo, and MakeMyTrip, apply your budget, and recommend the best timing within the allowed flexibility window.",
  },
];

function App() {
  const [query, setQuery] = useState("");
  const [messages, setMessages] = useState(initialMessages);
  const [loading, setLoading] = useState(false);

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
    <main className="app-shell">
      <section className="hero-panel">
        <p className="eyebrow">AI Travel Agent</p>
        <h1>Flight search that understands how people actually ask.</h1>
        <p className="hero-copy">
          Use plain English, mention your budget, ask for flexible timing, and
          get a cross-platform comparison with a best-fit recommendation.
        </p>

        <div className="prompt-list">
          {starterPrompts.map((prompt) => (
            <button
              key={prompt}
              type="button"
              className="prompt-chip"
              onClick={() => setQuery(prompt)}
            >
              {prompt}
            </button>
          ))}
        </div>
      </section>

      <section className="chat-panel">
        <div className="chat-window">
          {messages.map((message) => (
            <MessageBubble key={message.id} message={message} />
          ))}
          {loading ? (
            <div className="message-bubble assistant loading">
              <div className="message-meta">Travel Agent</div>
              <div className="message-text">
                Checking providers and comparing prices...
              </div>
            </div>
          ) : null}
        </div>

        <form className="composer" onSubmit={handleSubmit}>
          <label className="sr-only" htmlFor="travel-query">
            Travel query
          </label>
          <textarea
            id="travel-query"
            value={query}
            onChange={(event) => setQuery(event.target.value)}
            rows="3"
            placeholder="Find flights from Delhi to Mumbai on 20-03-2026 around 5:00 PM under 6000 with flexible timing."
          />
          <div className="composer-footer">
            <p>
              Supports time flexibility within +/- 2 hours and
              platform-by-platform price comparison.
            </p>
            <button type="submit" disabled={loading}>
              {loading ? "Searching..." : "Search Flights"}
            </button>
          </div>
        </form>
      </section>
    </main>
  );
}

export default App;
