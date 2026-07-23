export default function Content({ children }) {
  return (
    <main className="app-content">
      <div className="app-content-inner">
        {children}
      </div>
    </main>
  );
}