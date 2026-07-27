import "./SegmentedControl.css";

function joinClasses(...classes) {
  return classes.filter(Boolean).join(" ");
}

export default function SegmentedControl({
  options = [],
  value,
  onChange,
  size = "default",
  className = "",
  ariaLabel = "Select option",
}) {
  const normalizedSize = ["default", "compact"].includes(size)
    ? size
    : "default";

  function getOptionValue(option) {
    return typeof option === "object" ? option.value : option;
  }

  function getOptionLabel(option) {
    return typeof option === "object"
      ? option.label ?? option.value
      : option;
  }

  return (
    <div
      className={joinClasses(
        "qmi-segmented-control",
        `qmi-segmented-control--${normalizedSize}`,
        className
      )}
      role="group"
      aria-label={ariaLabel}
    >
      {options.map((option) => {
        const optionValue = getOptionValue(option);
        const optionLabel = getOptionLabel(option);
        const isActive = value === optionValue;

        return (
          <button
            key={optionValue}
            type="button"
            className={joinClasses(
              "qmi-segmented-control__option",
              isActive &&
                "qmi-segmented-control__option--active"
            )}
            aria-pressed={isActive}
            onClick={() => onChange?.(optionValue)}
          >
            {optionLabel}
          </button>
        );
      })}
    </div>
  );
}