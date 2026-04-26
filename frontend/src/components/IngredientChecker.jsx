import { useState } from 'react'

export default function IngredientChecker({ onCheck, hasProfile }) {
  const [ingredient, setIngredient] = useState('')
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState(null)

  const handleSubmit = async (e) => {
    e.preventDefault()
    if (!ingredient.trim()) return
    setLoading(true)
    setResult(null)
    try {
      const data = await onCheck(ingredient.trim())
      setResult(data)
    } catch (err) {
      setResult({ error: err.message || 'Something went wrong.' })
    } finally {
      setLoading(false)
    }
  }

  return (
    <section className="ingredient-checker">
      <div className="profile-panel-header">
        <div>
          <p className="conversation-kicker">Analysis</p>
          <h2 className="conversation-title">Ingredient Check</h2>
        </div>
        {!hasProfile && (
          <span className="profile-status">Add a health profile to personalise results</span>
        )}
      </div>

      <form className="ingredient-checker-form" onSubmit={handleSubmit}>
        <input
          type="text"
          className="ingredient-input"
          value={ingredient}
          onChange={(e) => setIngredient(e.target.value)}
          placeholder="Enter an ingredient, e.g. aspartame, gluten, soy…"
          disabled={loading}
        />
        <button type="submit" className="refresh-btn" disabled={loading || !ingredient.trim()}>
          {loading ? 'Checking…' : 'Check'}
        </button>
      </form>

      {result && !result.error && (
        <div className="ingredient-result">
          <p className="ingredient-result-text">{result.response}</p>
          {result.sources?.length > 0 && (
            <div className="ingredient-sources">
              {result.sources.map((s) => (
                <a
                  key={s.title}
                  href={s.url || '#'}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="source-link"
                >
                  {s.title}
                </a>
              ))}
            </div>
          )}
        </div>
      )}

      {result?.error && (
        <p className="ingredient-error">{result.error}</p>
      )}
    </section>
  )
}
