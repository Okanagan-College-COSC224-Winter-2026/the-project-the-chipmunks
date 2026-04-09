interface WeightSegment {
  name: string;
  weight: number;
}

const COLORS = ['#2B6CB0', '#2F855A', '#C05621', '#6B46C1', '#B83280', '#2C7A7B', '#9B2C2C', '#744210'];

export default function WeightBar({ segments }: { segments: WeightSegment[] }) {
  const total = segments.reduce((s, c) => s + c.weight, 0);
  const isValid = Math.abs(total - 100) < 0.01;

  return (
    <div style={{ marginBottom: 16 }}>
      <div style={{
        display: 'flex', height: 28, borderRadius: 6, overflow: 'hidden',
        border: '1px solid var(--background-tertiary, #b5b5b5)',
      }}>
        {segments.map((seg, i) => (
          <div
            key={i}
            title={`${seg.name}: ${seg.weight}%`}
            style={{
              width: `${seg.weight}%`,
              background: COLORS[i % COLORS.length],
              display: 'flex', alignItems: 'center', justifyContent: 'center',
              color: '#fff', fontSize: '0.7rem', fontWeight: 600,
              minWidth: seg.weight > 5 ? 'auto' : 0,
              transition: 'width 0.2s ease',
            }}
          >
            {seg.weight >= 8 ? `${seg.weight}%` : ''}
          </div>
        ))}
        {total < 100 && <div style={{ flex: 1, background: 'var(--background-secondary, #dcdcdc)' }} />}
      </div>
      <p style={{
        fontSize: '0.8rem', marginTop: 4, fontWeight: 600,
        color: isValid ? '#2F855A' : '#C53030',
      }}>
        Total: {total.toFixed(1)}% {isValid ? '\u2705' : '(must equal 100%)'}
      </p>
    </div>
  );
}
