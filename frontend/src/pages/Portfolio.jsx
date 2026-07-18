import {
  Activity,
  Database,
  PieChart,
  Trash2,
  Wallet
} from "lucide-react";

import Card from "../components/ui/Card";
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

function Portfolio({
  portfolio,
  form,
  setForm,
  savePosition,
  deletePosition,
  editingId,
  setEditingId,
  startEdit
}) {
  const rows = portfolio?.positions || [];

  function cancelEditing() {
    setEditingId(null);

    setForm({
      ticker: "",
      company: "",
      sector: "",
      quantity: "",
      average_price: "",
      current_price: "",
      notes: ""
    });
  }

  return (
    <>
      <div className="grid4">
        <Card
          title="Market Value"
          value={money(portfolio?.total_value)}
          subtitle="Current portfolio value"
          icon={<Wallet size={18} />}
        />

        <Card
          title="Cost Basis"
          value={money(portfolio?.total_cost)}
          subtitle="Invested capital"
          icon={<Database size={18} />}
        />

        <Card
          title="Total P/L"
          value={money(portfolio?.total_pl)}
          subtitle={pct(portfolio?.total_pl_pct)}
          icon={<Activity size={18} />}
        />

        <Card
          title="Largest Weight"
          value={pct(portfolio?.largest_position_weight)}
          subtitle="Concentration control"
          icon={<PieChart size={18} />}
        />
      </div>

      <Panel
        title={editingId ? "Edit Position" : "Add Position"}
        subtitle="Persistent SQLite portfolio engine"
      >
        <form
          className="form portfolio-form"
          onSubmit={savePosition}
        >
          <input
            placeholder="Ticker"
            value={form.ticker}
            onChange={(event) =>
              setForm({
                ...form,
                ticker: event.target.value
              })
            }
            required
          />

          <input
            placeholder="Company"
            value={form.company}
            onChange={(event) =>
              setForm({
                ...form,
                company: event.target.value
              })
            }
          />

          <input
            placeholder="Sector"
            value={form.sector}
            onChange={(event) =>
              setForm({
                ...form,
                sector: event.target.value
              })
            }
          />

          <input
            placeholder="Quantity"
            value={form.quantity}
            onChange={(event) =>
              setForm({
                ...form,
                quantity: event.target.value
              })
            }
            required
          />

          <input
            placeholder="Average price"
            value={form.average_price}
            onChange={(event) =>
              setForm({
                ...form,
                average_price: event.target.value
              })
            }
            required
          />

          <input
            placeholder="Current price"
            value={form.current_price}
            onChange={(event) =>
              setForm({
                ...form,
                current_price: event.target.value
              })
            }
          />

          <input
            className="wide-input"
            placeholder="Notes"
            value={form.notes}
            onChange={(event) =>
              setForm({
                ...form,
                notes: event.target.value
              })
            }
          />

          <button>
            {editingId ? "Save changes" : "Add position"}
          </button>

          {editingId && (
            <button
              type="button"
              className="secondary-button"
              onClick={cancelEditing}
            >
              Cancel
            </button>
          )}
        </form>
      </Panel>

      <Panel
        title="Portfolio Positions"
        subtitle={`${rows.length} positions · editable engine`}
      >
        <div className="table-head">
          <span>Ticker</span>
          <span>Company</span>
          <span>Sector</span>
          <span>Qty</span>
          <span>Avg</span>
          <span>Price</span>
          <span>Value</span>
          <span>P/L</span>
          <span>Weight</span>
          <span>Actions</span>
        </div>

        <div className="table">
          {rows.map((position) => (
            <div
              className="trow portfolio-row"
              key={position.id}
            >
              <b>{position.ticker}</b>

              <span>{position.company}</span>

              <span>{position.sector}</span>

              <span>{position.quantity}</span>

              <span>{money(position.average_price)}</span>

              <span>{money(position.current_price)}</span>

              <span>{money(position.value)}</span>

              <span
                className={
                  position.pl >= 0 ? "pos" : "neg"
                }
              >
                {money(position.pl)} · {pct(position.pl_pct)}
              </span>

              <span>{pct(position.weight)}</span>

              <div className="row-actions">
                <button onClick={() => startEdit(position)}>
                  Edit
                </button>

                <button
                  onClick={() =>
                    deletePosition(position.id)
                  }
                >
                  <Trash2 size={14} />
                </button>
              </div>
            </div>
          ))}
        </div>
      </Panel>

      <Panel
        title="Sector Allocation"
        subtitle="Exposure distribution"
      >
        <div className="metric-list">
          {(portfolio?.sector_allocation || []).map(
            (sector) => (
              <div key={sector.sector}>
                <strong>{sector.sector}</strong>

                <span>
                  {money(sector.value)} · {pct(sector.weight)}
                </span>
              </div>
            )
          )}
        </div>
      </Panel>
    </>
  );
}

export default Portfolio;