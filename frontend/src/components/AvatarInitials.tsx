interface Props {
  firstName: string;
  lastName: string;
  userId?: number;
  size?: number;
}

const PALETTE = [
  '#1F4E79','#2E75B6','#1B7A4A','#7B3F00',
  '#6A1493','#B71C1C','#01579B','#2E7D32',
];

function pickColour(userId = 0): string {
  return PALETTE[userId % PALETTE.length];
}

export default function AvatarInitials({ firstName, lastName, userId=0, size=40 }: Props) {
  const initials = `${firstName?.[0]??''}${lastName?.[0]??''}`.toUpperCase() || '?';
  const bg = pickColour(userId);
  const fontSize = Math.round(size * 0.38);

  return (
    <div style={{
      width: size,
      height: size,
      borderRadius: '50%',
      backgroundColor: bg,
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      color: '#fff',
      fontWeight: 700,
      fontSize: fontSize,
      flexShrink: 0,
      userSelect: 'none',
    }}>
      {initials}
    </div>
  );
}
