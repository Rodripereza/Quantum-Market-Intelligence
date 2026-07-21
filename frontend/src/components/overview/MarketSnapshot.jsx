import { ArrowUpRight, Radar } from "lucide-react";
import EmptyChartState from "./EmptyChartState";

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

function MarketSnapshot({ market, navigate }) {
  const assets = market?.assets || [];

  return (
    <section className="overview-surface market-snapshot">
      <div className="overview-section-heading">
        <div>
          <span className="section-kicker">
            LIVE INTELLIGENCE
          </span>

          <h2>Market Snapshot</h2>

          <p>
            Current prices and daily market movement
          </p>
        </div>

        <button
          className="overview-icon-action"
          onClick={() => navigate("market")}
          title="Open Market"
        >
          <ArrowUpRight size={17} />
        </button>
      </div>

      {assets.length > 0 ? (
        <div className="market-snapshot-list">
          {assets.slice(0, 6).map((asset) => (
            <div
              className="market-snapshot-row"
              key={asset.ticker}
            >
              <div className="market-symbol">
                <strong>{asset.ticker}</strong>
                <span>{asset.name}</span>
              </div>

              <div className="market-price">
                <strong>{money(asset.price)}</strong>

                <span
                  className={
                    asset.change_pct >= 0
                      ? "market-change positive"
                      : "market-change negative"
                  }
                >
                  {pct(asset.change_pct)}
                </span>
              </div>
            </div>
          ))}
        </div>
      ) : (
        <EmptyChartState
          icon={<Radar size={22} />}
          title="Market feed unavailable"
          description="Start the backend to load the current market snapshot."
          action="Open Market"
          onAction={() => navigate("market")}
        />
      )}
    </section>
  );
}

export default MarketSnapshot;