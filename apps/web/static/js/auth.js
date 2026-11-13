import { setBusy } from './ui.js';

const form = document.querySelector('[data-auth-form]');

if (form) {
  const inputs = [...form.querySelectorAll('.auth-field input')];
  const submit = form.querySelector('button[type="submit"]');
  const signup = form.action.includes('/register/');

  function messageFor(input) {
    const value = input.value.trim();
    if (input.name === 'username') {
      if (!value) return 'نام کاربری را وارد کن.';
      if (signup && value.length < 3) return 'نام کاربری حداقل ۳ حرف باشد.';
      if (!signup && value.includes('@') && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(value)) return 'ایمیل کامل نیست.';
    }
    if (input.name === 'email') {
      if (!value || !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(value)) return 'ایمیل کامل نیست.';
    }
    if (input.name === 'password') {
      if (!value) return 'گذرواژه را وارد کن.';
      if (signup && value.length < 10) return 'گذرواژه حداقل ۱۰ نویسه باشد.';
    }
    return '';
  }

  function validate(input) {
    const field = input.closest('.auth-field');
    const error = field.querySelector('.auth-field__error');
    const message = messageFor(input);
    field.dataset.state = message ? 'invalid' : 'valid';
    error.textContent = message;
    if (message) input.setAttribute('aria-invalid', 'true');
    else input.removeAttribute('aria-invalid');
    return !message;
  }

  for (const input of inputs) {
    input.addEventListener('blur', () => validate(input));
    input.addEventListener('input', () => {
      if (input.closest('.auth-field').dataset.state === 'invalid') validate(input);
      if (signup && input.name === 'password') updateStrength(input);
    });
  }

  function updateStrength(input) {
    const meter = form.querySelector('[data-password-strength]');
    if (!meter) return;
    const value = input.value;
    meter.hidden = !value;
    if (!value) return;
    const score = [value.length >= 10, /[a-z]/i.test(value), /\d/.test(value), /[^\p{L}\d]/u.test(value)].filter(Boolean).length;
    const level = Math.max(1, score);
    meter.dataset.strength = String(level);
    meter.querySelector('[data-strength-label]').textContent = ['ضعیف', 'ضعیف', 'متوسط', 'خوب', 'عالی'][level];
  }

  for (const toggle of form.querySelectorAll('[data-password-toggle]')) {
    toggle.addEventListener('click', () => {
      const input = document.getElementById(toggle.dataset.passwordToggle);
      const show = input.type === 'password';
      input.type = show ? 'text' : 'password';
      toggle.setAttribute('aria-pressed', String(show));
      toggle.setAttribute('aria-label', show ? 'پنهان کردن گذرواژه' : 'نمایش گذرواژه');
      input.focus();
    });
  }

  form.addEventListener('submit', event => {
    const valid = inputs.map(validate).every(Boolean);
    if (!valid) {
      event.preventDefault();
      inputs.find(input => input.getAttribute('aria-invalid') === 'true')?.focus();
      return;
    }
    setBusy(submit, true);
  });
}
