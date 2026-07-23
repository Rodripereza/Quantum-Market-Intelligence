import {
  ArrowDownRight,
  ArrowUpRight,
  BarChart3,
  Minus,
} from "lucide-react";

const FALLBACK_MOVERS = [
  {
    symbol: "NVDA",
    name: "NVIDIA",
    price: 142.61,
    change: 4.82,
    contribution: 1.16,
  },
  {
    symbol: "PLTR",
    name: "Palantir",
    price: 98.34,
    change: 3.47,
    contribution: 0.74,
  },
  {
    symbol: "RKLB",
    name: "Rocket Lab",
    price: 28.92,
    change: 2.68,
    contribution: 0.39,
  },
  {
    symbol: "NIO",
    name: "NIO",
    price: 6.41,
    change: -2.14,
    contribution: -0.58,
  },
  {
    symbol: "TSLA",
    name: "Tesla",
    price: 322.17,
    change: -1.32,
    contribution: -0.31,
  },
];

function formatPrice(value) {
  const numericValue = Number(value);

  if (Number.isNaN(numericValue)) {
    return "--";
  }

  return numericValue.toLocaleString("en-US", {
    style: "currency",
    currency: "USD",
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  });
}

function TopMoversCard({ movers }) {
  const safeMovers =
    Array.isArray(movers) && movers.length > 0
      ? movers
      : FALLBACK_MOVERS;

  return (
    <section className="overview-surface top-movers-card">
      <div className="overview-section-heading">
        <div>
          <span className="section-kicker">
            PORTFOLIO MOVERS
          </span>

          <h2>Top Movers</h2>

          <p>
            Assets generating the largest portfolio impact
          </p>
        </div>

        <div className="top-movers-status">
          <BarChart3 size={15} />
          Live ranking
        </div>
      </div>

      <div className="top-movers-table">
        <div className="top-movers-header">
          <span>Asset</span>
          <span>Price</span>
          <span>Change</span>
          <span>Contribution</span>
        </div>

        <div className="top-movers-list">
          {safeMovers.map((mover, index) => {
            const change = Number(mover.change ?? 0);
            const contribution = Number(
              mover.contribution ?? 0
            );

            const tone =
              change > 0
                ? "positive"
                : change < 0
                  ? "negative"
                  : "neutral";

            const ChangeIcon =
              change > 0
                ? ArrowUpRight
                : change < 0
                  ? ArrowDownRight
                  : Minus;

            return (
              <div
                key={`${mover.symbol}-${index}`}
                className="top-mover-row"
              >
                <div className="top-mover-asset">
                  <div className="top-mover-symbol">
                    {mover.symbol?.slice(0, 2) ?? "--"}
                  </div>

                  <div>
                    <strong>{mover.symbol ?? "--"}</strong>
                    <span>{mover.name ?? "Unknown asset"}</span>
                  </div>
                </div>

                <strong className="top-mover-price">
                  {formatPrice(mover.price)}
                </strong>

                <div className={`top-mover-change ${tone}`}>
                  <ChangeIcon size={15} />

                  <strong>
                    {change > 0 ? "+" : ""}
                    {change.toFixed(2)}%
                  </strong>
                </div>

                <div
                  className={`top-mover-contribution ${tone}`}
                >
                  <span>
                    {contribution > 0 ? "+" : ""}
                    {contribution.toFixed(2)}%
                  </span>

                  <div className="top-mover-impact-track">
                    <span
                      style={{
                        width: `${Math.min(
                          Math.abs(contribution) * 55,
                          100
                        )}%`,
                      }}
                    />
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      </div>

      <div className="top-movers-footer">
        <span>
          Ranked by percentage movement and portfolio contribution
        </span>

        <strong>{safeMovers.length} assets tracked</strong>
      </div>
    </section>
  );
}

export default TopMoversCard;