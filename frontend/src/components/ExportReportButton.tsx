import { useState } from 'react';
import { exportAssignmentPDF } from '../util/api';

interface Props {
  assignmentId: number;
  assignmentTitle: string;
}

export default function ExportReportButton({ assignmentId, assignmentTitle }: Props) {
  const [loading, setLoading] = useState(false);

  const handleExport = async () => {
    setLoading(true);
    try {
      const blob = await exportAssignmentPDF(assignmentId);
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `${assignmentTitle.replace(/\s+/g, '_')}_Report.pdf`;
      document.body.appendChild(a);
      a.click();
      a.remove();
      window.URL.revokeObjectURL(url);
    } catch (err) {
      console.error('Export failed:', err);
      alert('Failed to export report. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <button
      className="AssignmentAnalytics__csvBtn"
      onClick={handleExport}
      disabled={loading}
    >
      {loading ? 'Generating...' : '⬇ Export PDF Report'}
    </button>
  );
}
