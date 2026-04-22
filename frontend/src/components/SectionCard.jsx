export default function SectionCard({ title, children, accent = "sand" }) {
  return (
    <section className={`section-card accent-${accent}`}>
      <div className="section-card-header">
        <h2>{title}</h2>
      </div>
      <div className="section-card-body">{children}</div>
    </section>
  );
}
