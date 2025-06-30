let cart = [];

function searchProducts() {
    const query = document.getElementById('search_product').value;
    const searchResultsDiv = document.getElementById('search_results');
    searchResultsDiv.innerHTML = 'Carregando...';

    fetch(`/api/produtos?q=${query}`)
        .then(response => response.json())
        .then(data => {
            searchResultsDiv.innerHTML = '';
            if (data.length === 0) {
                searchResultsDiv.innerHTML = '<p style="padding: 10px; text-align: center;">Nenhum produto encontrado.</p>';
                return;
            }
            const ul = document.createElement('ul');
            data.forEach(product => {
                const li = document.createElement('li');
                const addButton = product.quantidade_estoque > 0 ?
                    `<button class="btn btn-primary" onclick="addToCart(${product.id}, '${product.nome}', ${product.valor}, ${product.quantidade_estoque})">Adicionar</button>` :
                    `<span class="no-stock-message">Sem Estoque</span>`;
                
                li.innerHTML = `
                    <span>${product.nome} (${product.marca}) - R$ ${product.valor.toFixed(2)} (Estoque: ${product.quantidade_estoque})</span>
                    ${addButton}
                `;
                ul.appendChild(li);
            });
            searchResultsDiv.appendChild(ul);
        })
        .catch(error => {
            console.error('Erro ao buscar produtos:', error);
            searchResultsDiv.innerHTML = '<p style="color: red; padding: 10px;">Erro ao carregar produtos.</p>';
        });
}

function addToCart(productId, productName, productValue, stockQuantity) {
    const existingItem = cart.find(item => item.id === productId);

    if (existingItem) {
        if (existingItem.quantity < stockQuantity) {
            existingItem.quantity++;
        } else {
            alert(`Limite de estoque (${stockQuantity}) para ${productName} atingido.`);
            return;
        }
    } else {
        if (stockQuantity === 0) {
            alert(`Produto ${productName} sem estoque.`);
            return;
        }
        cart.push({
            id: productId,
            name: productName,
            value: productValue,
            quantity: 1,
            stock: stockQuantity
        });
    }
    updateCartDisplay();
}

function updateCartDisplay() {
    const cartItemsUl = document.getElementById('cart_items');
    cartItemsUl.innerHTML = '';
    let totalVenda = 0;

    if (cart.length === 0) {
        cartItemsUl.innerHTML = '<li style="text-align: center; color: #888; padding: 10px;">Carrinho vazio.</li>';
    }

    cart.forEach(item => {
        const li = document.createElement('li');
        li.className = 'cart-item';
        const subtotal = item.quantity * item.value;
        totalVenda += subtotal;

        li.innerHTML = `
            <div class="item-details">
                <strong>${item.name}</strong> <br>
                <span>R$ ${item.value.toFixed(2)} x </span>
                <input type="number" value="${item.quantity}" min="1" max="${item.stock}" onchange="updateItemQuantity(${item.id}, this.value)">
                <span> = R$ ${subtotal.toFixed(2)}</span>
            </div>
            <button class="remove-item-btn" onclick="removeFromCart(${item.id})">Remover</button>
        `;
        cartItemsUl.appendChild(li);
    });

    document.getElementById('total_venda').textContent = totalVenda.toFixed(2);
}

function updateItemQuantity(productId, newQuantity) {
    newQuantity = parseInt(newQuantity);
    const item = cart.find(i => i.id === productId);

    if (item) {
        if (newQuantity < 1) {
            newQuantity = 1;
        }
        if (newQuantity > item.stock) {
            alert(`A quantidade máxima para ${item.name} é ${item.stock}.`);
            newQuantity = item.stock;
        }
        item.quantity = newQuantity;
    }
    updateCartDisplay();
}

function removeFromCart(productId) {
    cart = cart.filter(item => item.id !== productId);
    updateCartDisplay();
}

function finalizarVenda() {
    if (cart.length === 0) {
        alert('Adicione produtos ao carrinho para finalizar a venda.');
        return;
    }

    const vendaData = {
        itens: cart.map(item => ({
            produto_id: item.id,
            quantidade: item.quantity
        }))
    };

    fetch('/finalizar_venda', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(vendaData)
    })
    .then(response => response.json().then(data => ({ status: response.status, body: data })))
    .then(({ status, body }) => {
        if (status === 200 && body.success) {
            alert(`Venda finalizada com sucesso! ID da Venda: ${body.venda_id}. Total: R$ ${body.valor_total.toFixed(2)}`);
            cart = [];
            updateCartDisplay();
            openModal(body.venda_id);
        } else {
            alert(`Erro ao finalizar venda: ${body.message || 'Verifique o estoque ou os dados.'}`);
            console.error('Erro na resposta da API:', body);
        }
    })
    .catch(error => {
        console.error('Erro na requisição:', error);
        alert('Erro de conexão ao finalizar a venda.');
    });
}

function openModal(vendaId) {
    const modal = document.getElementById('venda_modal');
    const modalDetails = document.getElementById('modal_venda_details');
    modalDetails.innerHTML = 'Carregando detalhes da venda...';

    fetch(`/detalhes_venda/${vendaId}`)
        .then(response => response.text())
        .then(html => {
            const parser = new DOMParser();
            const doc = parser.parseFromString(html, 'text/html');
            const saleDetailsDiv = doc.querySelector('.sale-details-print');
            if (saleDetailsDiv) {
                modalDetails.innerHTML = saleDetailsDiv.innerHTML;
                const printBtn = modalDetails.querySelector('.btn-primary[onclick="window.print()"]');
                const newSaleBtn = modalDetails.querySelector('.btn-secondary[href*="venda_page"]');
                if (printBtn) printBtn.remove();
                if (newSaleBtn) newSaleBtn.remove();
            } else {
                modalDetails.innerHTML = '<p>Não foi possível carregar os detalhes da venda.</p>';
            }
            modal.style.display = 'block';
        })
        .catch(error => {
            console.error('Erro ao carregar detalhes da venda para o modal:', error);
            modalDetails.innerHTML = '<p style="color: red;">Erro ao carregar detalhes.</p>';
            modal.style.display = 'block';
        });
}

function closeModal() {
    const modal = document.getElementById('venda_modal');
    modal.style.display = 'none';
    document.getElementById('modal_venda_details').innerHTML = '';
}

function printVenda() {
    const modalDetailsContent = document.getElementById('modal_venda_details').innerHTML;
    const printWindow = window.open('', '_blank');
    printWindow.document.write('<html><head><title>Imprimir Venda</title>');
    printWindow.document.write('<link rel="stylesheet" href="/static/css/style.css">');
    printWindow.document.write('</head><body>');
    printWindow.document.write('<div class="sale-details-print">');
    printWindow.document.write(modalDetailsContent);
    printWindow.document.write('</div>');
    printWindow.document.write('<script>window.onload = function() { window.print(); window.onafterprint = function() { window.close(); } }</script>');
    printWindow.document.close();
}

document.addEventListener('DOMContentLoaded', updateCartDisplay);