import Panel from "../components/ui/Panel";

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
    maximumFractionDigits: 2
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

function Market({ market }) {
  const assets = market?.assets || [];

  return (
    <Panel
      title="Market Overview"
      subtitle={market?.source || "loading"}
    >
      {assets.map((asset) => (
        <div className="row" key={asset.ticker}>
          <div>
            <strong>{asset.ticker}</strong>
            <span>{asset.name}</span>
          </div>

          <div>
            <strong>{money(asset.price)}</strong>

            <em
              className={
                asset.change_pct >= 0 ? "pos" : "neg"
              }
            >
              {pct(asset.change_pct)}
            </em>
          </div>
        </div>
      ))}
    </Panel>
  );
}

export default Market;