import Card from "../ui/Card";
import "./KpiCard.css";

export default function KpiCard({
    title,
    value,
    subtitle,
    trend,
    icon,
    children
}) {
    return (
        <Card className="kpi-card">

            <div className="kpi-header">

                <div className="kpi-title">

                    {icon && (
                        <span className="kpi-icon">
                            {icon}
                        </span>
                    )}

                    <span>{title}</span>

                </div>

                {trend && (
                    <span className={`kpi-trend ${trend.type}`}>
                        {trend.value}
                    </span>
                )}

            </div>

            <div className="kpi-value">

                {value}

            </div>

            {subtitle && (

                <div className="kpi-subtitle">

                    {subtitle}

                </div>

            )}

            {children}

        </Card>
    );
}