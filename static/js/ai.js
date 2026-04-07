const titleInput = document.getElementById('title');
const descInput = document.getElementById('description');
const categorySelect = document.getElementById('category');
const suggestion = document.getElementById('suggestion');
const priorityBadge = document.getElementById('priority-badge');

async function getSuggestion() {
  const text = `${titleInput?.value || ''} ${descInput?.value || ''}`.trim();
  if (text.length < 5) return;

  const response = await fetch('/user/ai/suggest-category', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ text }),
  });

  if (!response.ok) return;
  const data = await response.json();

  suggestion.textContent = `Suggested: ${data.suggested_category}`;
  if (data.suggested_category) {
    categorySelect.value = data.suggested_category;
  }

  const isHigh = data.priority === 'High';
  priorityBadge.textContent = `Priority: ${data.priority}`;
  priorityBadge.className = `text-sm px-3 py-2 rounded-lg w-full text-center ${
    isHigh ? 'bg-red-100 text-red-700' : 'bg-green-100 text-green-700'
  }`;
}

descInput?.addEventListener('input', getSuggestion);
titleInput?.addEventListener('input', getSuggestion);
