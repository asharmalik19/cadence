import { formatDay, parseDay } from '../dates'

interface Props {
  currentDay: string
  realToday: string
  onFastForward: () => void
}

/** Shown on Today when the app's day is behind the calendar: days away happen, and catching up is one step. */
export function FastForwardBanner({ currentDay, realToday, onFastForward }: Props) {
  const behind = Math.round((parseDay(realToday).getTime() - parseDay(currentDay).getTime()) / 86_400_000)
  if (behind <= 0) return null
  return (
    <div className="ff-banner">
      <p>
        <strong>
          You’re {behind} {behind === 1 ? 'day' : 'days'} behind.
        </strong>{' '}
        The plan is still on {formatDay(currentDay)}; today is {formatDay(realToday)}.
      </p>
      <button className="btn" onClick={onFastForward}>
        Fast forward
      </button>
    </div>
  )
}
