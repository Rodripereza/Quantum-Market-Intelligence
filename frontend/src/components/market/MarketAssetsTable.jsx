import { ArrowDown, ArrowUp, Minus } from "lucide-react";

function formatPrice(value) {
  const numericValue = Number(value);

  if (!Number.isFinite(numericValue)) {
    return "--";
  }

  return numericValue.toLocaleString("en-US", {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  });
}

function formatPercentage(value) {
  const numericValue = Number(value);

  if (!Number.isFinite(numericValue)) {
    return "--";
  }

  return `${numericValue > 0 ? "+" : ""}${numericValue.toFixed(2)}%`;
}

function formatVolume(value) {
  const numericValue = Number(value);

  if (!Number.isFinite(numericValue)) {
    return "--";
  }

  return new Intl.NumberFormat("en-US", {
    notation: "compact",
    maximumFractionDigits: 1,
  }).format(numericValue);
}

function getTone(value) {
  const numericValue = Number(value);

  if (!Number.isFinite(numericValue) || numericValue === 0) {
    return "neutral";
  }

  return numericValue > 0 ? "positive" : "negative";
}

function ChangeIcon({ tone }) {
  if (tone === "positive") {
    return <ArrowUp size={13} strokeWidth={2.5} />;
  }

  if (tone === "negative") {
    return <ArrowDown size={13} strokeWidth={2.5} />;
  }

  return <Minus size={13} strokeWidth={2.5} />;
}

export default function MarketAssetsTable({ assets = [] }) {
  const safeAssets = Array.isArray(assets) ? assets : [];

  return (
    <section className="qmi-datagrid">
      <header className="qmi-datagrid__header">
        <div>
          <span className="qmi-datagrid__eyebrow">
            Cross-asset intelligence
          </span>

          <h2>Market Monitor</h2>

          <p>
            Live overview of the primary instruments monitored by QMI.
          </p>
        </div>

        <div className="qmi-datagrid__status">
          <span className="qmi-datagrid__status-dot" />
          Live data
        </div>
      </header>

      {safeAssets.length === 0 ? (
        <div className="qmi-datagrid__empty">
          No market assets available.
        </div>
      ) : (
        <div className="qmi-datagrid__viewport">
          <table className="qmi-datagrid__table">
            <thead>
              <tr>
                <th>Instrument</th>
                <th>Category</th>
                <th className="qmi-datagrid__numeric">Last</th>
                <th className="qmi-datagrid__numeric">Previous</th>
                <th className="qmi-datagrid__numeric">Change</th>
                <th className="qmi-datagrid__numeric">Volume</th>
                <th className="qmi-datagrid__numeric">Trend</th>
              </tr>
            </thead>

            <tbody>
              {safeAssets.map((asset) => {
                const tone = getTone(asset.change_pct);

                return (
                  <tr key={asset.provider_symbol || asset.ticker}>
                    <td>
                      <div className="qmi-datagrid__instrument">
                        <span className="qmi-datagrid__symbol">
                          {asset.ticker}
                        </span>

                        <span className="qmi-datagrid__name">
                          {asset.name || "--"}
                        </span>
                      </div>
                    </td>

                    <td>
                      <span className="qmi-datagrid__badge">
                        {asset.category || "Market"}
                      </span>
                    </td>

                    <td className="qmi-datagrid__numeric qmi-datagrid__price">
                      {formatPrice(asset.price)}
                    </td>

                    <td className="qmi-datagrid__numeric qmi-datagrid__muted">
                      {formatPrice(asset.previous_close)}
                    </td>

                    <td className="qmi-datagrid__numeric">
                      <span
                        className={`qmi-datagrid__change qmi-datagrid__change--${tone}`}
                      >
                        {formatPercentage(asset.change_pct)}
                      </span>
                    </td>

                    <td className="qmi-datagrid__numeric qmi-datagrid__muted">
                      {formatVolume(asset.volume)}
                    </td>

                    <td className="qmi-datagrid__numeric">
                      <span
                        className={`qmi-datagrid__trend qmi-datagrid__trend--${tone}`}
                        aria-label={`${tone} trend`}
                      >
                        <ChangeIcon tone={tone} />
                      </span>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}

      <footer className="qmi-datagrid__footer">
        <span>{safeAssets.length} instruments monitored</span>
        <span>Source: Yahoo Finance</span>
      </footer>
    </section>
  );
}