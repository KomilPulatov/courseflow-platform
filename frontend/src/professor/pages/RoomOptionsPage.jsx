import { useState } from "react";
import { useParams } from "react-router-dom";

import { request } from "../api.js";
import { Alert } from "../components/Alert.jsx";
import { useAsyncResource } from "../useAsyncResource.js";

export function RoomOptionsPage() {
  const { sectionId } = useParams();
  const [roomId, setRoomId] = useState("");
  const [preferenceRank, setPreferenceRank] = useState("1");
  const [message, setMessage] = useState("");
  const [errorMessage, setErrorMessage] = useState("");

  const { data, loading, error, reload } = useAsyncResource(async () => {
    const [detail, options] = await Promise.all([
      request(`/api/v1/professor/sections/${sectionId}`),
      request(`/api/v1/professor/sections/${sectionId}/room-options`),
    ]);
    return { detail, options };
  }, [sectionId]);

  async function onSubmit(event) {
    event.preventDefault();
    try {
      setErrorMessage("");
      const result = await request(`/api/v1/professor/sections/${sectionId}/room-preferences`, {
        method: "POST",
        body: JSON.stringify({
          room_id: Number(roomId),
          preference_rank: Number(preferenceRank),
        }),
      });
      setMessage(result.message);
      reload();
    } catch (submitError) {
      setErrorMessage(submitError.message);
    }
  }

  if (loading) return <div className="empty-state">Loading room pool...</div>;
  if (error) {
    return (
      <section className="content-card">
        <div className="content-card__header">
          <div>
            <div className="page-kicker">Professor / Room Options</div>
            <h2 className="content-card__title">Room Pool</h2>
          </div>
          <button className="button" type="button" onClick={reload}>
            Retry
          </button>
        </div>
        <div className="empty-state">{error}</div>
      </section>
    );
  }

  const { detail, options } = data;

  return (
    <div className="stack-lg">
      <Alert message={message} type="success" />
      <Alert message={errorMessage} type="error" />

      <section className="content-card">
        <div className="content-card__header">
          <div>
            <div className="page-kicker">Professor / Room Options</div>
            <h2 className="content-card__title">{detail.course_code} · Room Pool</h2>
            <p className="content-card__subtitle">
              Choose a room for section {detail.section_code}. Only allocated rooms are shown below.
            </p>
          </div>
        </div>
        <div className="meta-row">
          <span>Section {detail.section_code}</span>
          <span>Capacity {detail.capacity}</span>
          <span>{detail.room_selection_mode}</span>
          <span>{detail.status}</span>
        </div>
      </section>

      <section className="content-card">
        <div className="content-card__header">
          <div>
            <h3>Available Options</h3>
            <p className="content-card__subtitle">The list below comes from the admin room allocation pool.</p>
          </div>
        </div>
        <div className="option-list">
          {options.options.map((option) => (
            <article key={option.room_id} className="option-item">
              <div className="option-item__title">
                {option.building ? `${option.building}-` : ""}
                {option.room_number}
              </div>
              <div className="meta-row">
                <span>Room ID {option.room_id}</span>
                <span>Capacity {option.capacity}</span>
                <span>{option.room_type}</span>
              </div>
            </article>
          ))}
        </div>
      </section>

      <section className="content-card">
        <div className="content-card__header">
          <div>
            <h3>Submit Preference</h3>
            <p className="content-card__subtitle">Save the preferred room for this section.</p>
          </div>
        </div>
        <form className="form-grid" onSubmit={onSubmit}>
          <input
            type="number"
            min="1"
            placeholder="Room ID"
            value={roomId}
            onChange={(event) => setRoomId(event.target.value)}
            required
          />
          <input
            type="number"
            min="1"
            value={preferenceRank}
            onChange={(event) => setPreferenceRank(event.target.value)}
            required
          />
          <button className="button" type="submit">
            Save room preference
          </button>
        </form>
      </section>
    </div>
  );
}
