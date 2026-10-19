interface Props {
  message: string
  onRetry?: () => void
}

/** Calm, never red: what went wrong, that nothing changed, and a way to try again. */
export function ErrorNotice({ message, onRetry }: Props) {
  return (
    <div className="card error-notice" role="alert">
      <p>{message}</p>
      {onRetry && (
        <button className="btn btn-quiet" onClick={onRetry}>
          Try again
        </button>
      )}
    </div>
  )
}
