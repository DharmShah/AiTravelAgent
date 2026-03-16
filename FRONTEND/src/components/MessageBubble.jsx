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
    <section className="comparison-card">
      <div className="comparison-header">
        <div>
          <p className="eyebrow">Recommended Flight</p>
          <h3>{comparison.best_option.airline}</h3>
        </div>
        <div className="price-pill">
          {formatCurrency(comparison.best_option.price_inr)}
        </div>
      </div>

      <div className="comparison-grid">
        <article>
          <span>Departure</span>
          <strong>
            {formatTimeLabel(comparison.best_option.departure_time)}
          </strong>
        </article>
        <article>
          <span>Provider</span>
          <strong>{comparison.best_option.provider}</strong>
        </article>
        <article>
          <span>Route</span>
          <strong>
            {comparison.criteria.origin} to {comparison.criteria.destination}
          </strong>
        </article>
      </div>

      <div className="table-wrap">
        <table>
          <thead>
            <tr>
              <th>Platform</th>
              <th>Airline</th>
              <th>Departure</th>
              <th>Price</th>
            </tr>
          </thead>
          <tbody>
            {comparison.platform_comparison.map((item) => (
              <tr
                key={`${item.provider}-${item.airline}-${item.departure_time}`}
              >
                <td>{item.provider}</td>
                <td>{item.airline}</td>
                <td>{formatTimeLabel(item.departure_time)}</td>
                <td>{formatCurrency(item.price_inr)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <p className="assistant-note">{comparison.reasoning}</p>
    </section>
  );
}

export function MessageBubble({ message }) {
  return (
    <div className={`message-bubble ${message.role}`}>
      <div className="message-meta">
        {message.role === "assistant" ? "Travel Agent" : "You"}
      </div>
      <div className="message-text">{message.text}</div>
      {message.comparison ? (
        <FlightComparison comparison={message.comparison} />
      ) : null}
    </div>
  );
}
