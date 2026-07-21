import { TrendingUp } from "lucide-react";

function money(number, currency = "USD") {
  if (
    number === null ||
    number === undefined ||
    Number.isNaN(Number(number))
  ) {
    return "--";
  }

  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency,
    maximumFractionDigits: 2,
  }).format(number);
}

function pct(number) {
  if (
    number === null ||
    number === undefined ||
    Number.isNaN(Number(number))
  ) {
    return "--";
  }

  return `${Number(number || 0).toFixed(2)}%`;
}

function HeroValueCard({ portfolio }) {
  const totalPL = Number(portfolio?.total_pl || 0);
  const totalPLPct = Number(portfolio?.total_pl_pct || 0);

  const performanceClass =
    totalPL >= 0 ? "positive" : "negative";

  return (
    <article className="hero-value-card">
      <div className="hero-value-card__header">
        <span>Total portfolio value</span>

        <div className="hero-value-card__live">
          <span />
          Live
        </div>
      </div>

      <strong className="hero-value-card__value">
        {money(portfolio?.total_value)}
      </strong>

      <div
        className={`hero-value-card__performance ${performanceClass}`}
      >
        <TrendingUp size={16} />

        <span>
          {money(portfolio?.total_pl)} · {pct(totalPLPct)}
        </span>
      </div>

      <div className="hero-value-card__sparkline" aria-hidden="true">
        <span style={{ height: "28%" }} />
        <span style={{ height: "38%" }} />
        <span style={{ height: "34%" }} />
        <span style={{ height: "52%" }} />
        <span style={{ height: "61%" }} />
        <span style={{ height: "72%" }} />
        <span style={{ height: "84%" }} />
        <span style={{ height: "76%" }} />
        <span style={{ height: "92%" }} />
      </div>

      <div className="hero-value-card__footer">
        <span>Persistent portfolio engine</span>
        <strong>QMI v1.3</strong>
      </div>
    </article>
  );
}

export default HeroValueCard;