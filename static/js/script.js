// --- Lógica de Privacidade ---
function togglePrivacy() {
    const elements = document.querySelectorAll('.privacy-target');
    const icon = document.getElementById('eye-icon');
    elements.forEach(el => el.classList.toggle('blur-value'));
    
    if (icon.classList.contains('fa-eye')) {
        icon.classList.remove('fa-eye');
        icon.classList.add('fa-eye-slash');
    } else {
        icon.classList.remove('fa-eye-slash');
        icon.classList.add('fa-eye');
    }
}

// --- Alternância de Abas ---
function switchTab(tab) {
    const homeView = document.getElementById('view-home');
    const statsView = document.getElementById('view-stats');
    const btnHome = document.getElementById('btn-home');
    const btnStats = document.getElementById('btn-stats');

    if (tab === 'home') {
        homeView.style.display = 'block';
        statsView.style.display = 'none';
        btnHome.classList.add('active');
        btnStats.classList.remove('active');
    } else {
        homeView.style.display = 'none';
        statsView.style.display = 'block';
        btnHome.classList.remove('active');
        btnStats.classList.add('active');
        carregarGrafico();
    }
}

// --- Lógica de Categorias e Gasolina Inteligente ---
const categorias = {
    'entrada': [
        { icone: 'fa-burger', nome: 'iFood' },
        { icone: 'fa-motorcycle', nome: 'Uber' },
        { icone: 'fa-helmet-safety', nome: '99' },
        { icone: 'fa-box', nome: 'Particular' }
    ],
    'saida': [
        { icone: 'fa-gas-pump', nome: 'Gasolina' }, // Nome exato importa para a lógica
        { icone: 'fa-wrench', nome: 'Manutenção' },
        { icone: 'fa-utensils', nome: 'Almoço' },
        { icone: 'fa-mobile', nome: 'Internet' },
        { icone: 'fa-file-invoice', nome: 'Multa' }
    ]
};

function mudarTipo(tipo) {
    const container = document.getElementById('chipsContainer');
    const inputDesc = document.getElementById('inputDescricao');
    const camposGasolina = document.getElementById('camposGasolina');
    
    // Reset visual
    container.innerHTML = '';
    inputDesc.value = '';
    camposGasolina.style.display = 'none'; // Esconde gasolina por padrão

    if (categorias[tipo]) {
        categorias[tipo].forEach(cat => {
            const btn = document.createElement('div');
            btn.className = 'chip-cat';
            btn.innerHTML = `<i class="fas ${cat.icone} me-2"></i>${cat.nome}`;
            
            btn.onclick = function() {
                // Remove active de todos
                document.querySelectorAll('.chip-cat').forEach(c => c.classList.remove('active'));
                this.classList.add('active');
                
                inputDesc.value = cat.nome;

                // Lógica da Gasolina: Se clicou em Gasolina, mostra os campos extras
                if (cat.nome === 'Gasolina') {
                    camposGasolina.style.display = 'block';
                } else {
                    camposGasolina.style.display = 'none';
                }
            };
            container.appendChild(btn);
        });
    }
}

// --- Gráfico Chart.js ---
let chartInstance = null;
async function carregarGrafico() {
    try {
        const response = await fetch('/dados_grafico');
        const dados = await response.json();
        const ctx = document.getElementById('graficoSemanal').getContext('2d');
        
        if (chartInstance) chartInstance.destroy();

        chartInstance = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: dados.map(d => d.dia),
                datasets: [
                    { label: 'Ganhos', data: dados.map(d => d.entrada), backgroundColor: '#34d399', borderRadius: 4 },
                    { label: 'Gastos', data: dados.map(d => d.saida), backgroundColor: '#f87171', borderRadius: 4 }
                ]
            },
            options: {
                responsive: true,
                plugins: { legend: { position: 'bottom', labels: { color: '#cbd5e1' } } },
                scales: {
                    y: { beginAtZero: true, grid: { color: 'rgba(255,255,255,0.05)' }, ticks: { color: '#cbd5e1' } },
                    x: { grid: { display: false }, ticks: { color: '#cbd5e1' } }
                }
            }
        });
    } catch (e) {
        console.log("Erro ao carregar gráfico:", e);
    }
}

// Inicialização
document.addEventListener('DOMContentLoaded', () => {
    mudarTipo('entrada');
});