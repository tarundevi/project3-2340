const TOPICS = [
  { value: '', label: 'All Topics' },
  { value: 'macronutrients', label: 'Macronutrients' },
  { value: 'vitamins_minerals', label: 'Vitamins & Minerals' },
  { value: 'diet_plans', label: 'Diet Plans' },
  { value: 'weight_management', label: 'Weight Management' },
  { value: 'sports_nutrition', label: 'Sports Nutrition' },
  { value: 'hydration', label: 'Hydration' },
  { value: 'digestive_health', label: 'Digestive Health' },
  { value: 'food_safety', label: 'Food Safety' },
]

function TopicSelector({ value, onChange }) {
  return (
    <div style={{ marginBottom: '12px' }}>
      <label style={{ fontFamily: 'monospace', fontSize: '0.875rem', marginRight: '8px' }}>
        Topic:
      </label>
      <select
        value={value}
        onChange={(e) => onChange(e.target.value)}
        style={{
          padding: '6px 8px',
          border: '1px solid #000',
          fontFamily: 'monospace',
          fontSize: '0.875rem',
          background: '#fff',
          cursor: 'pointer',
        }}
      >
        {TOPICS.map((t) => (
          <option key={t.value} value={t.value}>
            {t.label}
          </option>
        ))}
      </select>
    </div>
  )
}

export default TopicSelector
