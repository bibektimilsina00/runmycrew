import { useSkills } from '../hooks/useSkills'

/**
 * Placeholder shell. PR 1 wires the route + nav entry; PR 2 builds the
 * full grid + create / delete flow on top of this skeleton.
 */
export function Skills() {
  const { data: skills = [], isLoading } = useSkills()

  return (
    <div className="px-8 py-10">
      <h1 className="text-2xl font-semibold tracking-tight text-text">Skills</h1>
      <p className="mt-1 text-sm text-text-mute">
        Reusable instruction bodies the AI agent can load on demand.
      </p>

      <div className="mt-8">
        {isLoading ? (
          <p className="text-sm text-text-faint">Loading…</p>
        ) : skills.length === 0 ? (
          <p className="text-sm text-text-faint">
            No skills yet. The full builder lands in PR 2.
          </p>
        ) : (
          <ul className="flex flex-col gap-1.5 font-mono text-[12px] text-text-mute">
            {skills.map(skill => (
              <li key={skill.id} className="rounded-[5px] border border-border-faint bg-bg px-3 py-2">
                {skill.name} — {skill.description || <em className="text-text-faint">no description</em>}
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  )
}
