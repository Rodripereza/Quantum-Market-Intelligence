import GlobalMarketBar from "../components/market/GlobalMarketBar";
import Panel from "../components/ui/Panel";
import MarketAssetsTable from "../components/market/MarketAssetsTable";

function formatPercentage(value) {
  const numericValue = Number(value);

  if (Number.isNaN(numericValue)) {
    return "--";
  }

  return `${numericValue > 0 ? "+" : ""}${numericValue.toFixed(2)}%`;
}

function Market({ market }) {
  const assets = Array.isArray(market?.assets)
    ? market.assets
    : [];

  const advancingAssets = assets.filter(
    (asset) => Number(asset.change_pct) > 0
  );

  const decliningAssets = assets.filter(
    (asset) => Number(asset.change_pct) < 0
  );

  const unchangedAssets = assets.filter(
    (asset) => Number(asset.change_pct) === 0
  );

  const strongestAsset =
    assets.length > 0
      ? [...assets].sort(
          (first, second) =>
            Number(second.change_pct) -
            Number(first.change_pct)
        )[0]
      : null;

  const weakestAsset =
    assets.length > 0
      ? [...assets].sort(
          (first, second) =>
            Number(first.change_pct) -
            Number(second.change_pct)
        )[0]
      : null;

  const averageChange =
    assets.length > 0
      ? assets.reduce(
          (total, asset) =>
            total + Number(asset.change_pct || 0),
          0
        ) / assets.length
      : 0;

  const marketTone =
    averageChange > 0.2
      ? "Positive"
      : averageChange < -0.2
      ? "Negative"
      : "Mixed";

  return (
    <>
      <GlobalMarketBar market={market} />

      <Panel
        title="Market Overview"
        subtitle={market?.source || "Loading market data"}
      >
        <section className="market-overview-grid">
          <article className="market-overview-card">
            <span className="market-overview-card__label">
              Market tone
            </span>

            <strong className="market-overview-card__value">
              {marketTone}
            </strong>

            <small className="market-overview-card__meta">
              Average move {formatPercentage(averageChange)}
            </small>
          </article>

          <article className="market-overview-card">
            <span className="market-overview-card__label">
              Advancers
            </span>

            <strong className="market-overview-card__value market-overview-card__value--positive">
              {advancingAssets.length}
            </strong>

            <small className="market-overview-card__meta">
              {decliningAssets.length} declining ·{" "}
              {unchangedAssets.length} unchanged
            </small>
          </article>

          <article className="market-overview-card">
            <span className="market-overview-card__label">
              Strongest asset
            </span>

            <strong className="market-overview-card__value">
              {strongestAsset?.ticker || "--"}
            </strong>

            <small className="market-overview-card__meta market-overview-card__meta--positive">
              {formatPercentage(strongestAsset?.change_pct)}
            </small>
          </article>

          <article className="market-overview-card">
            <span className="market-overview-card__label">
              Weakest asset
            </span>

            <strong className="market-overview-card__value">
              {weakestAsset?.ticker || "--"}
            </strong>

            <small className="market-overview-card__meta market-overview-card__meta--negative">
              {formatPercentage(weakestAsset?.change_pct)}
            </small>
          </article>

          <article className="market-overview-card">
            <span className="market-overview-card__label">
              Assets monitored
            </span>

            <strong className="market-overview-card__value">
              {assets.length}
            </strong>

            <small className="market-overview-card__meta">
              Global cross-asset universe
            </small>
          </article>

          <article className="market-overview-card">
            <span className="market-overview-card__label">
              Feed status
            </span>

            <strong className="market-overview-card__value market-overview-card__value--positive">
              {market?.status || "Unavailable"}
            </strong>

            <small className="market-overview-card__meta">
              {market?.source || "No source"}
            </small>
          </article>
        </section>
      </Panel>

       <MarketAssetsTable
          assets={assets}
      />
    </>
  );
}

export default Market;