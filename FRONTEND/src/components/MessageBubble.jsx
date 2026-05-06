function formatCurrency(amount) {
  if (typeof amount !== "number") {
    return "Price unavailable";
  }

  return new Intl.NumberFormat("en-IN", {
    style: "currency",
    currency: "INR",
    maximumFractionDigits: 0,
  }).format(amount);
}

function formatTimeLabel(value) {
  if (!value) {
    return "Flexible";
  }

  return value;
}

function FlightComparison({ comparison }) {
  return (
    <div className="mt-4 bg-cyan-500/10 border border-cyan-400/30 rounded-2xl p-5 space-y-4">
      {/* Best Option Header */}
      <div className="flex items-start justify-between gap-4">
        <div>
          <p className="text-xs font-bold text-cyan-400 uppercase tracking-wide">
            ⭐ Best Match
          </p>
          <h3 className="text-lg font-bold text-white mt-1">
            {comparison.best_option.airline}
          </h3>
        </div>
        <div className="px-3 py-2 bg-cyan-400/20 border border-cyan-400/50 rounded-lg">
          <p className="text-xl font-bold text-cyan-300">
            {formatCurrency(comparison.best_option.price_inr)}
          </p>
        </div>
      </div>

      {/* Key Details Grid */}
      <div className="grid grid-cols-3 gap-3">
        <div className="bg-slate-700/50 rounded-lg p-3">
          <p className="text-xs text-gray-400 uppercase font-semibold mb-1">
            Departure
          </p>
          <p className="text-sm font-bold text-white">
            {formatTimeLabel(comparison.best_option.departure_time)}
          </p>
        </div>
        <div className="bg-slate-700/50 rounded-lg p-3">
          <p className="text-xs text-gray-400 uppercase font-semibold mb-1">
            Provider
          </p>
          <p className="text-sm font-bold text-cyan-300">
            {comparison.best_option.provider}
          </p>
        </div>
        <div className="bg-slate-700/50 rounded-lg p-3">
          <p className="text-xs text-gray-400 uppercase font-semibold mb-1">
            Route
          </p>
          <p className="text-sm font-bold text-white">
            {comparison.criteria.origin.substring(0, 3).toUpperCase()} to{" "}
            {comparison.criteria.destination.substring(0, 3).toUpperCase()}
          </p>
        </div>
      </div>

      {/* Comparison Table */}
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-cyan-400/20">
              <th className="px-3 py-2 text-left text-xs font-bold text-cyan-400 uppercase">
                Platform
              </th>
              <th className="px-3 py-2 text-left text-xs font-bold text-cyan-400 uppercase">
                Airline
              </th>
              <th className="px-3 py-2 text-left text-xs font-bold text-cyan-400 uppercase">
                Time
              </th>
              <th className="px-3 py-2 text-right text-xs font-bold text-cyan-400 uppercase">
                Price
              </th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-700/30">
            {comparison.platform_comparison.map((item) => (
              <tr
                key={`${item.provider}-${item.airline}-${item.departure_time}`}
                className="hover:bg-slate-700/20"
              >
                <td className="px-3 py-2 text-white font-medium">
                  {item.provider}
                </td>
                <td className="px-3 py-2 text-white">{item.airline}</td>
                <td className="px-3 py-2 text-gray-300">
                  {formatTimeLabel(item.departure_time)}
                </td>
                <td className="px-3 py-2 text-right text-cyan-300 font-bold">
                  {formatCurrency(item.price_inr)}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Recommendation Note */}
      <div className="bg-slate-700/30 rounded-lg p-3 border border-slate-600/30">
        <p className="text-sm text-gray-300 leading-relaxed">
          <span className="text-cyan-400 font-semibold">
            💡 Why this flight?{" "}
          </span>
          {comparison.reasoning}
        </p>
      </div>
    </div>
  );
}

export function MessageBubble({ message }) {
  return (
    <div
      className={`flex mb-3 animate-fadeIn ${message.role === "user" ? "justify-end" : "justify-start"}`}
    >
      <div
        className={`max-w-[88%] md:max-w-[82%] ${
          message.role === "user"
            ? "bg-gradient-to-br from-cyan-500 to-blue-600 text-white rounded-3xl rounded-tr-lg"
            : "bg-slate-700/40 backdrop-blur-sm text-gray-100 rounded-3xl rounded-tl-lg border border-slate-600/20"
        } px-4 py-3`}
      >
        <div className="text-xs font-bold uppercase tracking-wider mb-1 opacity-70">
          {message.role === "assistant" ? "🤖 AI Agent" : "👤 You"}
        </div>
        <div className="text-sm leading-relaxed whitespace-pre-wrap break-words">
          {message.text}
        </div>

        {message.comparison ? (
          <FlightComparison comparison={message.comparison} />
        ) : null}
      </div>
    </div>
  );
}
