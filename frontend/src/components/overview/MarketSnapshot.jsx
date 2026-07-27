import {
  ArrowDownRight,
  ArrowUpRight,
  Minus,
  Radar,
} from "lucide-react";

import EmptyChartState from "./EmptyChartState";
import SectionHeader from "../ui/SectionHeader";
import Card, { CardBody } from "../ui/Card";

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

  const value = Number(number);

  return `${value > 0 ? "+" : ""}${value.toFixed(2)}%`;
}

function getTone(change) {
  const value = Number(change);

  if (Number.isNaN(value) || value === 0) {
    return "neutral";
  }

  return value > 0 ? "positive" : "negative";
}

function MarketSnapshot({ market, navigate }) {
  const assets = market?.assets || [];

  return (
    <Card
      className="overview-surface market-snapshot market-snapshot-pro"
>
      <SectionHeader
        eyebrow="LIVE INTELLIGENCE"
        title="Market Snapshot"
        subtitle="Real-time pricing and daily market movement"
        className="overview-section-heading market-snapshot-heading"
        actions={
          <button
            type="button"
            className="overview-icon-action"
            onClick={() => navigate("market")}
            title="Open Market"
        >
          <ArrowUpRight size={17} />
        </button>
      }
    />
    <CardBody>

      {assets.length > 0 ? (
        <>
          <div className="market-snapshot-columns">
            <span>Asset</span>
            <span>Price</span>
            <span>Change</span>
          </div>

          <div className="market-snapshot-list">
            {assets.slice(0, 6).map((asset) => {
              const tone = getTone(asset.change_pct);

              const ChangeIcon =
                tone === "positive"
                  ? ArrowUpRight
                  : tone === "negative"
                    ? ArrowDownRight
                    : Minus;

              return (
                <button
                  type="button"
                  className="market-snapshot-row"
                  key={asset.ticker}
                  onClick={() => navigate("market")}
                >
                  <div className="market-asset">
                    <span
                      className={`market-status-dot ${tone}`}
                      aria-hidden="true"
                    />

                    <div className="market-symbol">
                      <strong>{asset.ticker}</strong>
                      <span>{asset.name}</span>
                    </div>
                  </div>

                  <div className="market-price">
                    <strong>{money(asset.price)}</strong>
                  </div>

                  <div className={`market-change-chip ${tone}`}>
                    <ChangeIcon size={13} />
                    <span>{pct(asset.change_pct)}</span>
                  </div>
                </button>
              );
            })}
          </div>

          <div className="market-snapshot-footer">
            <span>Live market feed</span>

            <button
              type="button"
              onClick={() => navigate("market")}
            >
              Open full market
              <ArrowUpRight size={13} />
            </button>
          </div>
        </>
      ) : (
        <EmptyChartState
          icon={<Radar size={22} />}
          title="Market feed unavailable"
          description="Start the backend to load the current market snapshot."
          action="Open Market"
          onAction={() => navigate("market")}
        />
      )}
    </CardBody>
    </Card>
  );
}

export default MarketSnapshot;