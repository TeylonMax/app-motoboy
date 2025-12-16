// --- Lógica de Privacidade (Olho) ---
function togglePrivacy() {
    const elements = document.querySelectorAll('.privacy-target');
    const icon = document.getElementById('eye-icon');
    
    // Alterna a classe de desfoque
    elements.forEach(el => {
        el.classList.toggle('blur-value');
    });
    
    // Alterna o ícone
    if (icon.classList.contains('fa-eye')) {
        icon.classList.remove('fa-eye');
        icon.classList.add('fa-eye-slash');
    } else {
        icon.classList.remove('fa-eye-slash');
        icon.classList.add('fa-eye');
    }
}

// --- Lógica do Modal de Lançamentos ---

// Configuração das categorias (Aqui você edita os nomes e ícones)
const categorias = {
    'entrada': [
        { icone: 'fa-burger', nome: 'iFood' },
        { icone: 'fa-motorcycle', nome: 'Moto Uber' },
        { icone: 'fa-helmet-safety', nome: '99 Moto' },
        { icone: 'fa-box', nome: 'Entrega Part.' }
    ],
    'saida': [
        { icone: 'fa-gas-pump', nome: 'Gasolina' },
        { icone: 'fa-wrench', nome: 'Manutenção' },
        { icone: 'fa-utensils', nome: 'Almoço' },
        { icone: 'fa-mobile', nome: 'Internet' },
        { icone: 'fa-file-invoice', nome: 'Multa' }
    ]
};

// Função para renderizar os botões de categoria
function mudarTipo(tipo) {
    const container = document.getElementById('chipsContainer');
    const inputDesc = document.getElementById('inputDescricao');
    
    // Limpa container atual
    container.innerHTML = '';
    
    // Limpa input de descrição para não misturar
    inputDesc.value = '';

    // Verifica se o tipo existe no objeto
    if (categorias[tipo]) {
        categorias[tipo].forEach(cat => {
            // Cria o elemento visual da categoria (chip)
            const btn = document.createElement('div');
            btn.className = 'chip-cat';
            btn.innerHTML = `<i class="fas ${cat.icone} me-2"></i>${cat.nome}`;
            
            // Evento de clique no chip
            btn.onclick = function() {
                // Remove destaque de todos
                document.querySelectorAll('.chip-cat').forEach(c => c.classList.remove('active'));
                
                // Destaca o clicado
                this.classList.add('active');
                
                // Preenche o campo de texto automaticamente
                inputDesc.value = cat.nome;
            };
            
            container.appendChild(btn);
        });
    }
}

// Inicialização
document.addEventListener('DOMContentLoaded', () => {
    // Garante que comece com "entrada" selecionado
    mudarTipo('entrada');
    
    // Configuração básica do gráfico (se existir o canvas)
    const ctx = document.getElementById('graficoSemanal');
    if (ctx) {
        // Aqui você pode colocar a lógica do gráfico Chart.js se decidir usar
    }
});