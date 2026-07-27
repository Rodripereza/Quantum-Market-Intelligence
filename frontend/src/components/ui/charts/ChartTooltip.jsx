import "./ChartTooltip.css";

function defaultValueFormatter(value) {
  const numericValue = Number(value);

  if (Number.isNaN(numericValue)) {
    return "--";
  }

  return numericValue.toLocaleString("en-US", {
    maximumFractionDigits: 2,
  });
}

export default function ChartTooltip({
  active,
  payload,
  label,
  labelFormatter,
  valueFormatter = defaultValueFormatter,
  valueKey,
  className = "",
}) {
  if (!active || !payload?.length) {
    return null;
  }

  const selectedEntry = valueKey
    ? payload.find((entry) => entry.dataKey === valueKey)
    : payload[0];

  if (!selectedEntry) {
    return null;
  }

  const formattedLabel = labelFormatter
    ? labelFormatter(label)
    : label;

  const formattedValue = valueFormatter(
    selectedEntry.value,
    selectedEntry
  );

  return (
    <div
      className={[
        "qmi-chart-tooltip",
        className,
      ]
        .filter(Boolean)
        .join(" ")}
    >
      {formattedLabel !== undefined &&
        formattedLabel !== null && (
          <span className="qmi-chart-tooltip__label">
            {formattedLabel}
          </span>
        )}

      <strong className="qmi-chart-tooltip__value">
        {formattedValue}
      </strong>
    </div>
  );
}