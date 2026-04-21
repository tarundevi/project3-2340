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
    <div className="topic-selector">
      <span className="topic-label">Topic</span>
      <div className="topic-pills">
        {TOPICS.map((t) => (
          <button
            key={t.value}
            className={`topic-pill${value === t.value ? ' active' : ''}`}
            onClick={() => onChange(t.value)}
          >
            {t.label}
          </button>
        ))}
      </div>
    </div>
  )
}

export default TopicSelector
