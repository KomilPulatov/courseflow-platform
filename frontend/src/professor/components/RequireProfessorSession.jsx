import { LoginCard } from "./LoginCard.jsx";

export function RequireProfessorSession({
  profile,
  pageHeading,
  pageDescription,
  onSignIn,
  loading,
  children,
}) {
  if (!profile) {
    return (
      <div className="stack-lg">
        <section className="content-card content-card--hero">
          <div className="content-card__header">
            <div>
              <div className="page-kicker">Inha University in Tashkent</div>
              <h2 className="content-card__title">{pageHeading}</h2>
              <p className="content-card__subtitle">{pageDescription}</p>
            </div>
          </div>
          <div className="stat-strip">
            <article className="stat-tile">
              <div className="stat-tile__label">Session</div>
              <div className="stat-tile__value stat-tile__value--compact">Sign in required</div>
            </article>
            <article className="stat-tile">
              <div className="stat-tile__label">Access after sign in</div>
              <div className="stat-tile__value stat-tile__value--compact">Sections and room pool</div>
            </article>
            <article className="stat-tile">
              <div className="stat-tile__label">Data source</div>
              <div className="stat-tile__value stat-tile__value--compact">Assigned professor records</div>
            </article>
          </div>
        </section>
        <LoginCard onSubmit={onSignIn} loading={loading} />
      </div>
    );
  }

  return children;
}
