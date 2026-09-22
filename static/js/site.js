document.addEventListener('DOMContentLoaded', () => {
  const filters = document.querySelectorAll('.category-filter');
  const products = document.querySelectorAll('.product-col');
  filters.forEach(btn => btn.addEventListener('click', () => {
    filters.forEach(b => b.classList.remove('active', 'btn-dark'));
    filters.forEach(b => b.classList.add('btn-outline-dark'));
    btn.classList.add('active', 'btn-dark');
    btn.classList.remove('btn-outline-dark');
    const filter = btn.dataset.filter;
    products.forEach(card => {
      const show = filter === 'all' || card.dataset.category === filter;
      card.classList.toggle('d-none', !show);
    });
  }));
});
