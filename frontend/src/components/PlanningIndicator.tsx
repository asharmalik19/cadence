export function PlanningIndicator({ text }: { text: string }) {
  return (
    <div className="planning" role="status">
      <span className="planning-dot" />
      <span>{text}</span>
    </div>
  )
}
