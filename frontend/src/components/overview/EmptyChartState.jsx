import { ArrowUpRight } from "lucide-react";

function EmptyChartState({
  icon,
  title,
  description,
  action,
  onAction,
}) {
  return (
    <div className="empty-chart-state">
      <div className="empty-chart-icon">
        {icon}
      </div>

      <strong>{title}</strong>

      <p>{description}</p>

      {action && (
        <button onClick={onAction}>
          {action}
          <ArrowUpRight size={14} />
        </button>
      )}
    </div>
  );
}

export default EmptyChartState;