import { useState } from "react";
import { useAppContext } from "../../store/AppContext";

const initialState = {
  description: "",
  location: "",
  severity: "MEDIUM",
  category: "General",
};

export default function IncidentForm() {
  const [formState, setFormState] = useState(initialState);
  const [statusMessage, setStatusMessage] = useState("");
  const { submitIncident } = useAppContext();

  const handleChange = (event) => {
    const { name, value } = event.target;
    setFormState((current) => ({ ...current, [name]: value }));
  };

  const handleSubmit = async (event) => {
    event.preventDefault();

    if (!formState.description.trim()) {
      setStatusMessage("Add a short incident description before submitting.");
      return;
    }

    await submitIncident(formState);
    setStatusMessage("Report captured and assigned to dispatch.");
    setFormState(initialState);
  };

  return (
    <section className="panel form-panel">
      <div className="panel-heading">
        <p className="eyebrow">Rapid reporting</p>
        <h2>Log a new incident</h2>
      </div>
      <form onSubmit={handleSubmit} className="incident-form">
        <label htmlFor="incident-description">Description</label>
        <textarea id="incident-description" name="description" value={formState.description} onChange={handleChange} placeholder="Describe the event, suspects, vehicle details, and any immediate risk." />

        <label htmlFor="incident-location">Location</label>
        <input id="incident-location" name="location" value={formState.location} onChange={handleChange} placeholder="Neighborhood or landmark" />

        <div className="form-row">
          <div>
            <label htmlFor="incident-severity">Severity</label>
            <select id="incident-severity" name="severity" value={formState.severity} onChange={handleChange}>
              <option value="LOW">Low</option>
              <option value="MEDIUM">Medium</option>
              <option value="HIGH">High</option>
              <option value="CRITICAL">Critical</option>
            </select>
          </div>
          <div>
            <label htmlFor="incident-category">Category</label>
            <select id="incident-category" name="category" value={formState.category} onChange={handleChange}>
              <option value="General">General</option>
              <option value="Robbery">Robbery</option>
              <option value="Vehicle theft">Vehicle theft</option>
              <option value="Public disturbance">Public disturbance</option>
            </select>
          </div>
        </div>

        <button type="submit">Submit report</button>
        {statusMessage ? <p className="status-copy">{statusMessage}</p> : null}
      </form>
    </section>
  );
}
