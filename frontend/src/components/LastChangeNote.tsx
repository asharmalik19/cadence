export function LastChangeNote({ note }: { note: string | null }) {
  return (
    <div className="card change-note">
      <div className="label">Last change</div>
      <p style={{ marginTop: 8 }} className={note ? undefined : 'muted'}>
        {note ?? 'No changes yet.'}
      </p>
    </div>
  )
}
