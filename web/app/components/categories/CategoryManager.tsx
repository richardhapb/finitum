import { useMemo, useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import axios from 'axios';
import { categoriesApi } from '../../lib/api';
import type { Category } from '../../types/models';

const KEYWORD_SEPARATOR = /[,\n]/;

function parseKeywords(value: string): string[] {
  return value
    .split(KEYWORD_SEPARATOR)
    .map((keyword) => keyword.trim())
    .filter(Boolean);
}

function errorMessage(error: unknown, fallback: string): string {
  const detail: unknown = axios.isAxiosError(error) ? error.response?.data?.detail : undefined;
  if (typeof detail === 'string') {
    return detail;
  }
  if (Array.isArray(detail)) {
    // FastAPI validation errors arrive as a list of {loc, msg, type} objects.
    return detail
      .map((item) =>
        item && typeof item === 'object' && 'msg' in item
          ? String((item as { msg: unknown }).msg)
          : JSON.stringify(item),
      )
      .join(', ');
  }
  return fallback;
}

type KeywordEditorProps = {
  keywords: string[];
  onChange: (keywords: string[]) => void;
  inputId: string;
};

function KeywordEditor({ keywords, onChange, inputId }: KeywordEditorProps) {
  const [draft, setDraft] = useState('');

  const addDraft = () => {
    const parsed = parseKeywords(draft);
    if (!parsed.length) {
      return;
    }
    const existing = new Set(keywords.map((keyword) => keyword.toLowerCase()));
    const added = parsed.filter((keyword) => !existing.has(keyword.toLowerCase()));
    onChange([...keywords, ...added]);
    setDraft('');
  };

  return (
    <div>
      <div className="flex flex-wrap gap-2 mb-2">
        {keywords.length === 0 && (
          <p className="text-sm text-gray-500">
            No keywords yet. Transactions will only land here if you pick it by hand.
          </p>
        )}
        {keywords.map((keyword) => (
          <span
            key={keyword}
            className="inline-flex items-center gap-1 px-2 py-1 bg-gray-700 text-gray-100 rounded text-xs"
          >
            {keyword}
            <button
              type="button"
              aria-label={`Remove ${keyword}`}
              onClick={() => onChange(keywords.filter((item) => item !== keyword))}
              className="text-gray-400 hover:text-red-400 transition-colors"
            >
              ×
            </button>
          </span>
        ))}
      </div>
      <div className="flex flex-col gap-2 sm:flex-row">
        <input
          id={inputId}
          value={draft}
          onChange={(event) => setDraft(event.target.value)}
          onKeyDown={(event) => {
            if (event.key === 'Enter') {
              event.preventDefault();
              addDraft();
            }
          }}
          type="text"
          placeholder="Add a keyword, e.g. CONDOMINIO"
          className="min-w-0 flex-1 px-3 py-2 bg-gray-700 border border-gray-600 text-white rounded focus:outline-none focus:ring-2 focus:ring-blue-500 placeholder-gray-500"
        />
        <button
          type="button"
          onClick={addDraft}
          className="w-full shrink-0 px-4 py-2 bg-gray-700 hover:bg-gray-600 text-white rounded transition-colors sm:w-auto"
        >
          Add
        </button>
      </div>
      <p className="text-xs text-gray-500 mt-1">
        Separate several keywords with commas. Matching ignores case and accents.
      </p>
    </div>
  );
}

type CategoryRowProps = {
  category: Category;
  isEditing: boolean;
  onEdit: () => void;
  onCancel: () => void;
  onSave: (payload: { name: string; keywords: string[] }) => void;
  onReset: () => void;
  onDelete: () => void;
  isSaving: boolean;
};

function CategoryRow({
  category,
  isEditing,
  onEdit,
  onCancel,
  onSave,
  onReset,
  onDelete,
  isSaving,
}: CategoryRowProps) {
  const [name, setName] = useState(category.name);
  const [keywords, setKeywords] = useState<string[]>(category.patterns);

  const startEditing = () => {
    setName(category.name);
    setKeywords(category.patterns);
    onEdit();
  };

  if (!isEditing) {
    return (
      <div className="py-4 border-b border-gray-700 last:border-b-0">
        <div className="flex items-start justify-between gap-4">
          <div className="min-w-0">
            <div className="flex items-center gap-2 flex-wrap">
              <span className="text-white font-medium">{category.name}</span>
              {category.is_custom && (
                <span className="text-xs px-2 py-0.5 rounded-full bg-emerald-900 text-emerald-200">
                  Custom
                </span>
              )}
              {category.is_modified && (
                <span className="text-xs px-2 py-0.5 rounded-full bg-blue-900 text-blue-200">
                  Edited
                </span>
              )}
            </div>
            <p className="text-sm text-gray-400 mt-1 break-words">
              {category.patterns.length
                ? category.patterns.join(' · ')
                : 'No keywords — never matched automatically'}
            </p>
          </div>
          <button
            type="button"
            onClick={startEditing}
            className="shrink-0 px-3 py-1.5 bg-gray-700 hover:bg-gray-600 text-white rounded text-sm transition-colors"
          >
            Edit
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="py-4 border-b border-gray-700 last:border-b-0">
      <div className="space-y-3">
        <div>
          <label
            htmlFor={`category-name-${category.id}`}
            className="block text-sm font-medium text-gray-300 mb-1"
          >
            Name
          </label>
          <input
            id={`category-name-${category.id}`}
            value={name}
            onChange={(event) => setName(event.target.value)}
            type="text"
            className="w-full px-3 py-2 bg-gray-700 border border-gray-600 text-white rounded focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
          {!category.is_custom && (
            <p className="text-xs text-gray-500 mt-1">
              Built-in category — your changes stay private to your account.
            </p>
          )}
        </div>

        <div>
          <span className="block text-sm font-medium text-gray-300 mb-1">Keywords</span>
          <KeywordEditor
            keywords={keywords}
            onChange={setKeywords}
            inputId={`category-keyword-${category.id}`}
          />
        </div>

        <div className="flex flex-wrap gap-2 pt-1">
          <button
            type="button"
            onClick={() => onSave({ name, keywords })}
            disabled={isSaving}
            className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded transition-colors disabled:bg-gray-600"
          >
            {isSaving ? 'Saving...' : 'Save'}
          </button>
          <button
            type="button"
            onClick={onCancel}
            className="px-4 py-2 bg-gray-700 hover:bg-gray-600 text-white rounded transition-colors"
          >
            Cancel
          </button>
          {!category.is_custom && category.is_modified && (
            <button
              type="button"
              onClick={onReset}
              className="px-4 py-2 bg-gray-700 hover:bg-gray-600 text-yellow-200 rounded transition-colors"
            >
              Reset to defaults
            </button>
          )}
          {category.is_custom && (
            <button
              type="button"
              onClick={onDelete}
              className="px-4 py-2 bg-red-700 hover:bg-red-600 text-white rounded transition-colors"
            >
              Delete
            </button>
          )}
        </div>
      </div>
    </div>
  );
}

export function CategoryManager() {
  const queryClient = useQueryClient();
  const [editingId, setEditingId] = useState<number | null>(null);
  const [filter, setFilter] = useState('');
  const [showCreator, setShowCreator] = useState(false);
  const [newName, setNewName] = useState('');
  const [newKeywords, setNewKeywords] = useState<string[]>([]);
  const [status, setStatus] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const { data: categories = [], isLoading, error: loadError } = useQuery({
    queryKey: ['categories'],
    queryFn: categoriesApi.getAll,
  });

  const refreshCategories = () => {
    queryClient.invalidateQueries({ queryKey: ['categories'] });
  };

  const refreshTransactions = () => {
    queryClient.invalidateQueries({ queryKey: ['expenses'] });
    queryClient.invalidateQueries({ queryKey: ['transferences'] });
  };

  const updateMutation = useMutation({
    mutationFn: ({ id, name, keywords }: { id: number; name: string; keywords: string[] }) =>
      categoriesApi.update(id, { name, patterns: keywords }),
    onSuccess: (category) => {
      setEditingId(null);
      setError(null);
      setStatus(
        `Saved "${category.name}". Re-apply keywords below to update transactions you already have.`,
      );
      refreshCategories();
      refreshTransactions();
    },
    onError: (mutationError: unknown) => {
      setStatus(null);
      setError(errorMessage(mutationError, 'Could not save the category'));
    },
  });

  const createMutation = useMutation({
    mutationFn: categoriesApi.create,
    onSuccess: (category) => {
      setNewName('');
      setNewKeywords([]);
      setShowCreator(false);
      setError(null);
      setStatus(`Created "${category.name}".`);
      refreshCategories();
    },
    onError: (mutationError: unknown) => {
      setStatus(null);
      setError(errorMessage(mutationError, 'Could not create the category'));
    },
  });

  const resetMutation = useMutation({
    mutationFn: categoriesApi.reset,
    onSuccess: (category) => {
      setEditingId(null);
      setError(null);
      setStatus(`"${category.name}" is back to its defaults.`);
      refreshCategories();
      refreshTransactions();
    },
    onError: (mutationError: unknown) => {
      setStatus(null);
      setError(errorMessage(mutationError, 'Could not reset the category'));
    },
  });

  const deleteMutation = useMutation({
    mutationFn: categoriesApi.remove,
    onSuccess: (response) => {
      setEditingId(null);
      setError(null);
      setStatus(
        response.reassigned_expenses
          ? `Category deleted. ${response.reassigned_expenses} transaction(s) moved to "Otros".`
          : 'Category deleted.',
      );
      refreshCategories();
      refreshTransactions();
    },
    onError: (mutationError: unknown) => {
      setStatus(null);
      setError(errorMessage(mutationError, 'Could not delete the category'));
    },
  });

  const recategorizeMutation = useMutation({
    mutationFn: categoriesApi.recategorize,
    onSuccess: (response) => {
      setError(null);
      setStatus(
        `Re-applied keywords: ${response.expenses_updated} expense(s) and ` +
          `${response.transferences_updated} transfer(s) recategorized.`,
      );
      refreshTransactions();
    },
    onError: (mutationError: unknown) => {
      setStatus(null);
      setError(errorMessage(mutationError, 'Could not re-apply the keywords'));
    },
  });

  const visibleCategories = useMemo(() => {
    const needle = filter.trim().toLowerCase();
    if (!needle) {
      return categories;
    }
    return categories.filter(
      (category) =>
        category.name.toLowerCase().includes(needle) ||
        category.patterns.some((pattern) => pattern.toLowerCase().includes(needle)),
    );
  }, [categories, filter]);

  const handleCreate = () => {
    if (!newName.trim()) {
      setError('Enter a name for the category');
      return;
    }
    createMutation.mutate({ name: newName.trim(), patterns: newKeywords });
  };

  const handleDelete = (category: Category) => {
    const confirmed = window.confirm(
      `Delete "${category.name}"? Its transactions move to "Otros".`,
    );
    if (confirmed) {
      deleteMutation.mutate(category.id);
    }
  };

  return (
    <div className="space-y-6">
      <div className="bg-gray-800 rounded-lg p-6">
        <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <h2 className="text-xl font-semibold text-white">Categories</h2>
            <p className="text-gray-400 text-sm mt-1">
              Keywords decide where an imported transaction lands. Edit any category — including
              the built-in ones — or add your own.
            </p>
          </div>
          <button
            type="button"
            onClick={() => recategorizeMutation.mutate()}
            disabled={recategorizeMutation.isPending}
            className="shrink-0 px-4 py-2 bg-emerald-600 hover:bg-emerald-700 text-white rounded transition-colors disabled:bg-gray-600"
          >
            {recategorizeMutation.isPending ? 'Applying...' : 'Re-apply to existing transactions'}
          </button>
        </div>

        {status && <p className="mt-4 text-sm text-emerald-300">{status}</p>}
        {error && <p className="mt-4 text-sm text-red-400">{error}</p>}
        {loadError && (
          <p className="mt-4 text-sm text-red-400">Could not load your categories.</p>
        )}
      </div>

      <div className="bg-gray-800 rounded-lg p-6">
        <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between mb-4">
          <input
            value={filter}
            onChange={(event) => setFilter(event.target.value)}
            type="search"
            placeholder="Filter by name or keyword"
            className="w-full sm:max-w-xs px-3 py-2 bg-gray-700 border border-gray-600 text-white rounded focus:outline-none focus:ring-2 focus:ring-blue-500 placeholder-gray-500"
          />
          <button
            type="button"
            onClick={() => setShowCreator((value) => !value)}
            className="shrink-0 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded transition-colors"
          >
            {showCreator ? 'Cancel' : 'New category'}
          </button>
        </div>

        {showCreator && (
          <div className="mb-6 p-4 bg-gray-900 rounded border border-gray-700 space-y-3">
            <div>
              <label htmlFor="new-category-name" className="block text-sm font-medium text-gray-300 mb-1">
                Name
              </label>
              <input
                id="new-category-name"
                value={newName}
                onChange={(event) => setNewName(event.target.value)}
                type="text"
                placeholder="e.g. Pets"
                className="w-full px-3 py-2 bg-gray-700 border border-gray-600 text-white rounded focus:outline-none focus:ring-2 focus:ring-blue-500 placeholder-gray-500"
              />
            </div>
            <div>
              <span className="block text-sm font-medium text-gray-300 mb-1">Keywords</span>
              <KeywordEditor
                keywords={newKeywords}
                onChange={setNewKeywords}
                inputId="new-category-keyword"
              />
            </div>
            <button
              type="button"
              onClick={handleCreate}
              disabled={createMutation.isPending}
              className="px-4 py-2 bg-emerald-600 hover:bg-emerald-700 text-white rounded transition-colors disabled:bg-gray-600"
            >
              {createMutation.isPending ? 'Creating...' : 'Create category'}
            </button>
          </div>
        )}

        {isLoading ? (
          <p className="text-gray-400">Loading categories...</p>
        ) : visibleCategories.length === 0 ? (
          <p className="text-gray-400">No category matches "{filter}".</p>
        ) : (
          <div>
            {visibleCategories.map((category) => (
              <CategoryRow
                // Remount on save so the editor picks up the stored values.
                key={`${category.id}-${category.patterns.join('|')}-${category.name}`}
                category={category}
                isEditing={editingId === category.id}
                onEdit={() => {
                  setEditingId(category.id);
                  setStatus(null);
                  setError(null);
                }}
                onCancel={() => setEditingId(null)}
                onSave={({ name, keywords }) =>
                  updateMutation.mutate({ id: category.id, name, keywords })
                }
                onReset={() => resetMutation.mutate(category.id)}
                onDelete={() => handleDelete(category)}
                isSaving={updateMutation.isPending}
              />
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
