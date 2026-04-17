import { useState, useEffect, useCallback } from 'react';
import { useParams } from 'react-router-dom';
import CriterionCard, { CriterionData } from '../components/CriterionCard';
import WeightBar from '../components/WeightBar';
import StatusMessage from '../components/StatusMessage';
import Button from '../components/Button';
import { getRubricBuilder, upsertRubric, getRubricTemplates, applyRubricTemplate } from '../util/api';
import './RubricBuilderPage.css';

interface TemplateOption {
  id: number;
  name: string;
  template_name: string;
  criteria: CriterionData[];
}

interface RubricCriterionPayload {
  id?: number;
  name: string;
  description: string;
  max_score: number;
  weight: number;
  position: number;
}

interface RubricPayload {
  name: string;
  criteria: RubricCriterionPayload[];
  is_template?: boolean;
  template_name?: string;
}

export default function RubricBuilderPage() {
  const { assignmentId } = useParams<{ assignmentId: string }>();
  const assignId = Number(assignmentId);

  const [rubricName, setRubricName] = useState('');
  const [criteria, setCriteria] = useState<CriterionData[]>([]);
  const [, setRubricId] = useState<number | null>(null);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [successMsg, setSuccessMsg] = useState('');
  const [saveAsTemplate, setSaveAsTemplate] = useState(false);
  const [templateName, setTemplateName] = useState('');
  const [templates, setTemplates] = useState<TemplateOption[]>([]);
  const [loadingTemplates, setLoadingTemplates] = useState(false);

  const loadRubric = useCallback(async () => {
    try {
      const resp = await getRubricBuilder(assignId);
      if (resp && resp.ok) {
        const data = await resp.json();
        if (data.rubric) {
          setRubricId(data.rubric.id);
          setRubricName(data.rubric.name || data.rubric.template_name || '');
          setCriteria(
            (data.rubric.criteria || [])
              .sort((a: CriterionData, b: CriterionData) => a.position - b.position)
          );
        }
      }
    } catch (err) {
      console.error('Failed to load rubric', err);
    }
  }, [assignId]);

  useEffect(() => { loadRubric(); }, [loadRubric]);

  const loadTemplates = useCallback(async () => {
    setLoadingTemplates(true);
    try {
      const resp = await getRubricTemplates();
      if (resp && resp.ok) {
        const data = await resp.json();
        setTemplates(data.templates || []);
      }
    } catch (err) {
      console.error('Failed to load templates', err);
    }
    setLoadingTemplates(false);
  }, []);

  useEffect(() => { loadTemplates(); }, [loadTemplates]);

  const handleChange = (index: number, field: keyof CriterionData, value: string | number) => {
    setCriteria(prev => prev.map((c, i) => (i === index ? { ...c, [field]: value } : c)));
  };

  const handleAdd = () => {
    setCriteria(prev => [
      ...prev,
      { name: '', description: '', max_score: 10, weight: 0, position: prev.length },
    ]);
  };

  const handleDelete = (index: number) => {
    setCriteria(prev =>
      prev.filter((_, i) => i !== index).map((c, i) => ({ ...c, position: i }))
    );
  };

  const handleMoveUp = (index: number) => {
    if (index === 0) return;
    setCriteria(prev => {
      const arr = [...prev];
      [arr[index - 1], arr[index]] = [arr[index], arr[index - 1]];
      return arr.map((c, i) => ({ ...c, position: i }));
    });
  };

  const handleMoveDown = (index: number) => {
    setCriteria(prev => {
      if (index >= prev.length - 1) return prev;
      const arr = [...prev];
      [arr[index], arr[index + 1]] = [arr[index + 1], arr[index]];
      return arr.map((c, i) => ({ ...c, position: i }));
    });
  };

  const handleSave = async () => {
    setError(null);
    setSuccessMsg('');

    if (!rubricName.trim()) {
      setError('Rubric name is required.');
      return;
    }
    if (criteria.length === 0) {
      setError('At least one criterion is required.');
      return;
    }

    const totalWeight = criteria.reduce((s, c) => s + c.weight, 0);
    if (Math.abs(totalWeight - 100) > 0.01) {
      setError(`Weights must sum to 100%. Currently: ${totalWeight.toFixed(1)}%`);
      return;
    }

    for (const c of criteria) {
      if (!c.name.trim()) {
        setError('All criteria must have a name.');
        return;
      }
    }

    setSaving(true);
    try {
      const payload: RubricPayload = {
        name: rubricName,
        criteria: criteria.map((c, i) => ({
          ...(c.id ? { id: c.id } : {}),
          name: c.name,
          description: c.description,
          max_score: c.max_score,
          weight: c.weight,
          position: i,
        })),
      };

      if (saveAsTemplate) {
        payload.is_template = true;
        payload.template_name = templateName.trim() || rubricName;
      }

      const resp = await upsertRubric(assignId, payload as unknown as Record<string, unknown>);
      if (resp && resp.ok) {
        const data = await resp.json();
        if (data.rubric) {
          setRubricId(data.rubric.id);
          setCriteria(
            (data.rubric.criteria || [])
              .sort((a: CriterionData, b: CriterionData) => a.position - b.position)
          );
        }
        setSuccessMsg('Rubric saved successfully!');
        if (saveAsTemplate) loadTemplates();
      } else {
        const data = await resp.json().catch(() => ({}));
        setError(data.msg ? JSON.stringify(data.msg) : 'Failed to save rubric.');
      }
    } catch (err) {
      console.error('Save error', err);
      setError('Failed to save rubric.');
    }
    setSaving(false);
  };

  const handleApplyTemplate = async (templateId: number) => {
    setError(null);
    setSuccessMsg('');
    try {
      const resp = await applyRubricTemplate(templateId, assignId);
      if (resp && resp.ok) {
        const data = await resp.json();
        if (data.rubric) {
          setRubricId(data.rubric.id);
          setRubricName(data.rubric.name || data.rubric.template_name || '');
          setCriteria(
            (data.rubric.criteria || [])
              .sort((a: CriterionData, b: CriterionData) => a.position - b.position)
          );
        }
        setSuccessMsg('Template applied!');
      } else {
        setError('Failed to apply template.');
      }
    } catch (err) {
      console.error('Apply template error', err);
      setError('Failed to apply template.');
    }
  };

  const weightSegments = criteria.map(c => ({ name: c.name || '(unnamed)', weight: c.weight }));

  return (
    <div className="rubric-builder-page">
      <h1>Rubric Builder</h1>

      {templates.length > 0 && (
        <div className="rb-template-section">
          <label className="rb-template-label">Load from template:</label>
          <select
            defaultValue=""
            onChange={e => {
              const id = parseInt(e.target.value);
              if (id) handleApplyTemplate(id);
              e.target.value = '';
            }}
          >
            <option value="" disabled>{loadingTemplates ? 'Loading...' : 'Select a template...'}</option>
            {templates.map(t => (
              <option key={t.id} value={t.id}>{t.template_name || t.name}</option>
            ))}
          </select>
        </div>
      )}

      {error && <StatusMessage message={error} type="error" />}
      {successMsg && <StatusMessage message={successMsg} type="success" />}

      <div className="rb-name-section">
        <label>
          Rubric Name
          <input
            value={rubricName}
            onChange={e => setRubricName(e.target.value)}
            placeholder="e.g. Peer Review Rubric"
          />
        </label>
      </div>

      {criteria.length > 0 && <WeightBar segments={weightSegments} />}

      {criteria.map((c, i) => (
        <CriterionCard
          key={c.id ?? `new-${i}`}
          criterion={c}
          index={i}
          onChange={handleChange}
          onDelete={handleDelete}
          onMoveUp={handleMoveUp}
          onMoveDown={handleMoveDown}
          isFirst={i === 0}
          isLast={i === criteria.length - 1}
        />
      ))}

      <div className="rb-actions">
        <Button onClick={handleAdd}>+ Add Criterion</Button>
      </div>

      <div className="rb-template-save">
        <label className="rb-checkbox-label">
          <input
            type="checkbox"
            checked={saveAsTemplate}
            onChange={e => setSaveAsTemplate(e.target.checked)}
          />
          Save as reusable template
        </label>
        {saveAsTemplate && (
          <input
            className="rb-template-name-input"
            value={templateName}
            onChange={e => setTemplateName(e.target.value)}
            placeholder="Template name (optional, defaults to rubric name)"
          />
        )}
      </div>

      <div className="rb-save-section">
        <Button onClick={handleSave}>
          {saving ? 'Saving...' : 'Save Rubric'}
        </Button>
      </div>
    </div>
  );
}
