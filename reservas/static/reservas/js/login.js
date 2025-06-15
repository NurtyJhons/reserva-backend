document.addEventListener("DOMContentLoaded", () => {
  const form = document.getElementById('login-form');
  const messageEl = document.getElementById('message');
  const ownerDashboardUrl = document.body.dataset.ownerDashboardUrl;
  const customerCreateUrl = document.body.dataset.customerCreateUrl;

  form.addEventListener('submit', async (e) => {
    e.preventDefault();
    messageEl.textContent = '';

    const formData = new FormData(form);
    const data = Object.fromEntries(formData.entries());

    try {
      const response = await fetch('/api/auth/login/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(data),
      });

      if (response.ok) {
        const json = await response.json();
        localStorage.setItem('access_token', json.access);
        localStorage.setItem('refresh_token', json.refresh);
        messageEl.style.color = 'green';
        messageEl.textContent = 'Login realizado com sucesso!';

        const userTypeRes = await fetch('/api/auth/user-type/', {
          method: 'GET',
          headers: { 'Authorization': 'Bearer ' + json.access }
        });

        const userTypeData = await userTypeRes.json();
        const groups = userTypeData.groups;

        setTimeout(() => {
          if (groups.includes('owners')) {
            window.location.href = ownerDashboardUrl;
          } else {
            window.location.href = customerCreateUrl;
          }
        }, 1500);
      } else {
        const errorData = await response.json();
        messageEl.style.color = 'red';
        messageEl.textContent = 'Erro: ' + JSON.stringify(errorData);
      }
    } catch (error) {
      messageEl.style.color = 'red';
      messageEl.textContent = 'Erro na conexão com o servidor.';
    }
  });
});