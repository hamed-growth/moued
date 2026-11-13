export function setBusy(button, busy) {
  button.disabled = busy;
  button.setAttribute('aria-busy', String(busy));
}

export function showToast(message, kind = 'info') {
  const toast = document.createElement('div');
  toast.className = `alert alert--${kind} toast`;
  toast.setAttribute('role', 'status');
  toast.textContent = message;
  document.body.append(toast);
  window.setTimeout(() => toast.remove(), 3500);
}
