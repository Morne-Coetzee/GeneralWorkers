// ============================================================
// MAIN.JS — General UI interactions
// ============================================================

document.addEventListener('DOMContentLoaded', function () {

  // ── Hamburger Menu ──────────────────────────────────────────
  const hamburger = document.querySelector('.hamburger');
  const navMenu   = document.querySelector('.navbar-nav');

  if (hamburger && navMenu) {
    hamburger.addEventListener('click', function () {
      hamburger.classList.toggle('open');
      navMenu.classList.toggle('open');
    });

    // Close menu when a link is clicked
    navMenu.querySelectorAll('a').forEach(function (link) {
      link.addEventListener('click', function () {
        hamburger.classList.remove('open');
        navMenu.classList.remove('open');
      });
    });

    // Close menu on outside click
    document.addEventListener('click', function (e) {
      if (!hamburger.contains(e.target) && !navMenu.contains(e.target)) {
        hamburger.classList.remove('open');
        navMenu.classList.remove('open');
      }
    });
  }

  // ── Auto-dismiss flash messages ──────────────────────────────
  const flashMessages = document.querySelectorAll('.flash');
  flashMessages.forEach(function (flash) {
    setTimeout(function () {
      flash.style.transition = 'opacity 0.5s ease';
      flash.style.opacity = '0';
      setTimeout(function () {
        flash.remove();
      }, 500);
    }, 4500);
  });

  // ── Register page: user type selection ──────────────────────
  const userTypeCards = document.querySelectorAll('.user-type-card');
  const userTypeInput = document.getElementById('user_type_hidden');
  const registerFormStep = document.getElementById('register-form-step');
  const userTypeStep     = document.getElementById('user-type-step');

  if (userTypeCards.length && userTypeInput) {
    userTypeCards.forEach(function (card) {
      card.addEventListener('click', function () {
        const type = card.dataset.type;
        userTypeInput.value = type;

        // Visual selection
        userTypeCards.forEach(c => c.classList.remove('selected'));
        card.classList.add('selected');

        // Update form theme class
        if (registerFormStep) {
          registerFormStep.className = registerFormStep.className
            .replace(/\btheme-\w+\b/g, '')
            .trim();
          registerFormStep.classList.add('theme-' + (type === 'employer' ? 'emp' : 'wkr'));
        }

        // Show form step
        if (userTypeStep && registerFormStep) {
          userTypeStep.style.display = 'none';
          registerFormStep.style.display = 'block';
          registerFormStep.scrollIntoView({ behavior: 'smooth', block: 'start' });
        }
      });
    });
  }

  // ── Back button on register form ─────────────────────────────
  const backBtn = document.getElementById('back-to-type');
  if (backBtn && userTypeStep && registerFormStep) {
    backBtn.addEventListener('click', function () {
      registerFormStep.style.display = 'none';
      userTypeStep.style.display = 'block';
    });
  }

  // ── Apply form toggle ────────────────────────────────────────
  const applyToggles = document.querySelectorAll('.apply-toggle-btn');
  applyToggles.forEach(function (btn) {
    btn.addEventListener('click', function () {
      const targetId = btn.dataset.target;
      const form = document.getElementById(targetId);
      if (form) {
        const isHidden = form.style.display === 'none' || form.style.display === '';
        form.style.display = isHidden ? 'block' : 'none';
        btn.textContent = isHidden ? 'Cancel' : 'Apply Now';
      }
    });
  });

  // ── Confirm delete ───────────────────────────────────────────
  const deleteForms = document.querySelectorAll('.confirm-delete');
  deleteForms.forEach(function (form) {
    form.addEventListener('submit', function (e) {
      const msg = form.dataset.confirm || 'Are you sure you want to delete this?';
      if (!confirm(msg)) {
        e.preventDefault();
      }
    });
  });

  // ── Character counter for textareas ──────────────────────────
  document.querySelectorAll('textarea[maxlength]').forEach(function (ta) {
    const max = parseInt(ta.getAttribute('maxlength'), 10);
    const counter = document.createElement('div');
    counter.className = 'form-hint';
    counter.style.textAlign = 'right';
    counter.textContent = '0 / ' + max;
    ta.parentNode.appendChild(counter);

    ta.addEventListener('input', function () {
      counter.textContent = ta.value.length + ' / ' + max;
    });
  });

  // ── Active nav link highlight ─────────────────────────────────
  const currentPath = window.location.pathname;
  document.querySelectorAll('.navbar-nav a').forEach(function (link) {
    if (link.getAttribute('href') === currentPath) {
      link.classList.add('active');
    }
  });

});

// ── Skill pill toggle (fallback for browsers without :has()) ─────────────
document.querySelectorAll('.skill-pill').forEach(function(pill) {
  var cb = pill.querySelector('input[type="checkbox"]');
  if (!cb) return;
  function sync() {
    pill.classList.toggle('checked', cb.checked);
  }
  sync();
  pill.addEventListener('click', function() {
    cb.checked = !cb.checked;
    sync();
  });
});
