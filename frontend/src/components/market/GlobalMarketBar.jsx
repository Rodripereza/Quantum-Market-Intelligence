export default function GlobalMarketBar({ market }) {
  if (!market?.assets?.length) {
    return null;
  }

  return (
    <section className="global-market-bar">
      {market.assets.map((asset) => {
        const positive = asset.change_pct > 0;
        const negative = asset.change_pct < 0;

        return (
          <div
            key={asset.ticker}
            className="market-ticker"
          >
            <span className="ticker-symbol">
              {asset.ticker}
            </span>

            <span className="ticker-price">
              {asset.price?.toFixed(2)}
            </span>

            <span
              className={
                positive
                  ? "ticker-change positive"
                  : negative
                  ? "ticker-change negative"
                  : "ticker-change"
              }
            >
              {asset.change_pct > 0 ? "+" : ""}
              {asset.change_pct?.toFixed(2)}%
            </span>
          </div>
        );
      })}
    </section>
  );
}