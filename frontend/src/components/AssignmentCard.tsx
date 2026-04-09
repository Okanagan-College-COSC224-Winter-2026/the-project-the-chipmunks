import "./AssignmentCard.css";

interface Props {
  onClick?: () => void;
  children?: React.ReactNode;
  id: number | string;
  dueDate?: string;
}

export default function AssignmentCard(props: Props) {
  const formatDate = (dateStr?: string) => {
    if (!dateStr) return null;

    const date = new Date(dateStr);
    return date.toLocaleDateString("en-US", {
      month: "short",
      day: "numeric",
    });
  };

  const getStatus = (dateStr?: string) => {
    if (!dateStr) return "No Date";

    const now = new Date();
    const due = new Date(dateStr);

    return due < now ? "Past Due" : "Active";
  };

  const status = getStatus(props.dueDate);
  const formattedDate = formatDate(props.dueDate);

  return (
    <div
      onClick={() => {
        window.location.href = `/assignment/${props.id}`;
      }}
      className="A_Card"
    >
      <img src="/icons/document.svg" alt="document" />

      <div className="A_Card_Content">
        <div className="A_Card_Title">{props.children}</div>

        {/* ✅ Due Date */}
        {formattedDate && (
          <div className="A_Card_Date">Due {formattedDate}</div>
        )}

        {/* ✅ Status Badge */}
        <div className={`A_Card_Status ${status.replace(" ", "_")}`}>
          {status}
        </div>
      </div>
    </div>
  );
}