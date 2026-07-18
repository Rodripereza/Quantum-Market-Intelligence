import Panel from "../components/ui/Panel";

function AI({ ai }) {
  return (
    <Panel
      title="AI Intelligence"
      subtitle={ai?.status || "loading"}
    >
      <p>{ai?.message}</p>

      <div className="chips">
        {(ai?.modules || []).map((module) => (
          <span key={module}>
            {module}
          </span>
        ))}
      </div>
    </Panel>
  );
}

export default AI;