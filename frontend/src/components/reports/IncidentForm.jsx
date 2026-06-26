export default function IncidentForm() {
  return (
    <section className="panel">
      <h2>Report Incident</h2>
      <form>
        <label htmlFor="incident-description">Description</label>
        <textarea id="incident-description" name="description" />
        <button type="submit">Submit</button>
      </form>
    </section>
  );
}
