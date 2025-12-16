document.addEventListener("DOMContentLoaded", function() {
    carregarGrafico();
    
    // Recupera estado da privacidade (se o usuário deixou escondido antes)
    if (localStorage.getItem('saldoOculto') === 'true') {
        alternarPrivacidade(false); // False para não inverter, apenas aplicar
    }
});

// --- Função 1: Modo Privacidade (Esconder Valores) ---
let oculto = false;

function alternarPrivacidade(inverter = true) {
    if (inverter) {
        oculto = !oculto;
        // Salva a preferência no navegador do usuário
        localStorage.setItem('saldoOculto', oculto);
    } else {
        oculto = true;
    }

    const valores = document.querySelectorAll('.valor-mascara');
    const icone = document.getElementById('icone-olho');

    valores.forEach(elemento => {
        if (oculto) {
            // Guarda o valor original num atributo 'data-valor' se ainda não tiver
            if (!elemento.getAttribute('data-original')) {
                elemento.setAttribute('data-original', elemento.innerText);
            }
            elemento.innerText = '----';
        } else {
            // Restaura o valor original
            if (elemento.getAttribute('data-original')) {
                elemento.innerText = elemento.getAttribute('data-original');
            }
        }
    });

    // Troca o ícone
    if (icone) {
        icone.className = oculto ? 'fas fa-eye-slash' : 'fas fa-eye';
    }
}

// --- Função 2: Gráfico com Chart.js ---
function carregarGrafico() {
    fetch('/dados_grafico')
        .then(response => response.json())
        .then(dados => {
            const ctx = document.getElementById('graficoSemanal').getContext('2d');
            
            new Chart(ctx, {
                type: 'bar',
                data: {
                    labels: dados.labels,
                    datasets: [
                        {
                            label: 'Ganhos',
                            data: dados.entradas,
                            backgroundColor: '#00f2c3',
                            borderRadius: 5,
                            borderSkipped: false
                        },
                        {
                            label: 'Gastos',
                            data: dados.saidas,
                            backgroundColor: '#fd5d93',
                            borderRadius: 5,
                            borderSkipped: false
                        }
                    ]
                },
                options: {
                    responsive: true,
                    plugins: {
                        legend: { labels: { color: 'white' } } // Legenda branca
                    },
                    scales: {
                        y: {
                            beginAtZero: true,
                            grid: { color: '#2b3553' }, // Linhas do grid sutis
                            ticks: { color: '#9a9a9a' }
                        },
                        x: {
                            grid: { display: false },
                            ticks: { color: '#9a9a9a' }
                        }
                    }
                }
            });
        })
        .catch(error => console.error('Erro ao carregar gráfico:', error));
}