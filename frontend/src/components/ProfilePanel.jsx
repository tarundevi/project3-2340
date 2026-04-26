import { useEffect, useState } from 'react'

export default function ProfilePanel({ profile, loading, saving, onSave }) {
  const [draft, setDraft] = useState(profile?.raw_text || '')

  useEffect(() => {
    setDraft(profile?.raw_text || '')
  }, [profile?.raw_text])

  const handleSubmit = async (event) => {
    event.preventDefault()
    await onSave(draft)
  }

  const hasProfile = Boolean(profile?.raw_text?.trim())

  return (
    <section className="profile-panel">
      <div className="profile-panel-header">
        <div>
          <p className="conversation-kicker">Personalization</p>
          <h2 className="conversation-title">Health Profile</h2>
        </div>
        <span className={`profile-status${hasProfile ? ' active' : ''}`}>
          {hasProfile ? 'Profile active' : 'No profile yet'}
        </span>
      </div>

      <form className="profile-form" onSubmit={handleSubmit}>
        <textarea
          className="profile-textarea"
          value={draft}
          onChange={(event) => setDraft(event.target.value)}
          placeholder="Describe your health conditions, allergies, intolerances, medications or dietary restrictions, and goals in plain English."
          rows={6}
          disabled={loading || saving}
        />

        {profile?.summary?.length ? (
          <div className="profile-summary">
            {profile.summary.map((item) => (
              <p key={item}>{item}</p>
            ))}
          </div>
        ) : null}

        <button type="submit" className="refresh-btn" disabled={loading || saving}>
          {saving ? 'Saving…' : 'Save Profile'}
        </button>
      </form>
    </section>
  )
}
