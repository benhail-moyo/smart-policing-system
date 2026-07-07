import IncidentForm from "../components/reports/IncidentForm";
import { useAppContext } from "../store/AppContext";

export default function IncidentsPage() {
  const { incidents } = useAppContext();

  return (
    <div className="page-stack">
      <section className="panel">
        <p className="eyebrow">Incident reporting</p>
        <h2>Log and review reported events</h2>
        <p className="page-copy">Use the submission form to capture descriptions and triage outcomes.</p>
      </section>
      <div className="incident-layout">
        <IncidentForm />
        <section className="panel">
          <h3>Recent submissions</h3>
          {incidents.length === 0 ? (
            <p className="page-copy">No incident records have been loaded yet.</p>
          ) : (
            <ul className="incident-list">
              {incidents.map((incident) => (
                <li key={incident.id || incident.description}>
                  <strong>{incident.description}</strong>
                  <span>{incident.location || "Location pending"}</span>
                </li>
              ))}
            </ul>
          )}
        </section>
      </div>
    </div>
  );
}
