// frontend/app.js
//
// This script powers the RFID business card ordering UI. It orchestrates
// fetching templates from the catalog service, capturing user details,
// rendering previews, managing the cart and ultimately submitting the
// order to the checkout service. The flow is implemented without any
// external dependencies to ensure it runs in constrained environments.


const ENDPOINTS = {
    catalog: '/api/catalog',
    cart: '/api/cart',
    checkout: '/api/checkout',
    email: '/api/email',
    orders: '/api/orders',
};

document.addEventListener('DOMContentLoaded', () => {
    // Section DOM references
    const sections = {
        select: document.getElementById('select-template-section'),
        details: document.getElementById('details-section'),
        preview: document.getElementById('preview-section'),
        cart: document.getElementById('cart-section'),
        checkout: document.getElementById('checkout-section'),
        confirmation: document.getElementById('confirmation-section'),
    };

    function showSection(name) {
        Object.keys(sections).forEach(key => {
            if (key === name) {
                sections[key].classList.remove('hidden');
            } else {
                sections[key].classList.add('hidden');
            }
        });
    }

    // State variables
    let templates = [];
    let selectedTemplate = null;
    let cart = [];

    // DOM elements
    const templatesContainer = document.getElementById('templates-container');
    const templateNextBtn = document.getElementById('template-next-btn');
    const detailsForm = document.getElementById('details-form');
    const previewContainer = document.getElementById('card-preview');
    const addCartBtn = document.getElementById('add-cart-btn');
    const cartItemsContainer = document.getElementById('cart-items');
    const checkoutBtn = document.getElementById('checkout-btn');
    const confirmBtn = document.getElementById('confirm-btn');
    const checkoutSummary = document.getElementById('checkout-summary');

    document.getElementById('nav-home').addEventListener('click', (e) => {
        e.preventDefault();
        showSection('select');
    });

    // Fetch template data from the catalog service
    function loadTemplates() {
        fetch(ENDPOINTS.catalog)
            .then(res => res.json())
            .then(data => {
                templates = data.templates || [];
                renderTemplates();
            })
            .catch(err => {
                console.error('Failed to fetch templates', err);
            });
    }

    // Render the list of templates as clickable cards
    function renderTemplates() {
        templatesContainer.innerHTML = '';
        templates.forEach(tpl => {
            const card = document.createElement('div');
            card.className = 'template-card';
            card.style.backgroundColor = tpl.color;
            card.innerHTML = `<img src="assets/university-logo.jpg" alt="Logo" class="tpl-logo" />
                <h3>${tpl.name}</h3>
                <p>${tpl.description}</p>`;
            card.addEventListener('click', () => {
                selectedTemplate = tpl;
                // Highlight selection
                document.querySelectorAll('.template-card').forEach(el => el.classList.remove('selected'));
                card.classList.add('selected');
                templateNextBtn.disabled = false;
            });
            templatesContainer.appendChild(card);
        });
    }

    // Gather values from the details form
    function getFormValues() {
        return {
            student_id: document.getElementById('student_id').value.trim(),
            name: document.getElementById('name').value.trim(),
            institute: document.getElementById('institute').value.trim(),
            phone: document.getElementById('phone').value.trim(),
            email: document.getElementById('email').value.trim(),
            room: document.getElementById('room').value.trim(),
        };
    }

    // Create the visual card preview using the selected template and form values
    function renderPreview() {
        const values = getFormValues();
        previewContainer.innerHTML = ''; // clear old preview
        previewContainer.classList.add('preview-card');
        if (!selectedTemplate) return;

        previewContainer.style.backgroundColor = selectedTemplate.color;
        previewContainer.style.position = 'relative'; // ensure absolute logo positions correctly

        // Add university logo
        const logo = document.createElement('img');
        logo.src = '/assets/university-logo.jpg'; // <-- your logo file path
        logo.alt = 'University Logo';
        logo.className = 'preview-logo';
        previewContainer.appendChild(logo);

        // Add text lines
        const lines = [
            values.student_id,
            values.name,
            values.institute,
            values.phone,
            values.email,
            values.room,
        ];
        lines.forEach(text => {
            const line = document.createElement('div');
            line.className = 'line';
            line.textContent = text;
            previewContainer.appendChild(line);
        });
    }


    // Load current cart from the cart service
    function loadCart() {
        fetch(ENDPOINTS.cart)
            .then(res => res.json())
            .then(data => {
                cart = data.items || [];
                renderCart();
            })
            .catch(err => {
                console.error('Failed to fetch cart', err);
            });
    }

    // Render the cart items and update the checkout button state
    function renderCart() {
        cartItemsContainer.innerHTML = '';
        if (!cart || cart.length === 0) {
            cartItemsContainer.innerHTML = '<p>Your cart is empty.</p>';
            checkoutBtn.disabled = true;
            return;
        }
        checkoutBtn.disabled = false;
        cart.forEach(item => {
            const wrapper = document.createElement('div');
            wrapper.className = 'cart-item';
            const info = document.createElement('div');
            info.className = 'info';
            info.innerHTML = `<strong>${item.name}</strong> – ${item.template_id}`;
            const removeBtn = document.createElement('button');
            removeBtn.textContent = 'Remove';
            removeBtn.addEventListener('click', () => {
                removeCartItem(item.item_id);
            });
            const actions = document.createElement('div');
            actions.className = 'actions';
            actions.appendChild(removeBtn);
            wrapper.appendChild(info);
            wrapper.appendChild(actions);
            cartItemsContainer.appendChild(wrapper);
        });
    }

    function removeCartItem(itemId) {
        fetch(`${ENDPOINTS.cart}/${itemId}`, { method: 'DELETE' })
            .then(res => {
                if (!res.ok) throw new Error('Delete failed');
                return res.json();
            })
            .then(() => loadCart())
            .catch(err => console.error(err));
    }

    // Render checkout summary
    function renderCheckoutSummary() {
        checkoutSummary.innerHTML = '';
        if (!cart || cart.length === 0) {
            checkoutSummary.innerHTML = '<p>No items to checkout.</p>';
            return;
        }
        const list = document.createElement('ul');
        cart.forEach(item => {
            const li = document.createElement('li');
            li.textContent = `${item.name} – ${item.template_id}`;
            list.appendChild(li);
        });
        const customer = getFormValues();
        const customerInfo = document.createElement('div');
        customerInfo.innerHTML = `
            <h3>Customer Details</h3>
            <p><strong>ID:</strong> ${customer.student_id}</p>
            <p><strong>Name:</strong> ${customer.name}</p>
            <p><strong>Institute:</strong> ${customer.institute}</p>
            <p><strong>Phone:</strong> ${customer.phone}</p>
            <p><strong>Email:</strong> ${customer.email}</p>
            <p><strong>Room:</strong> ${customer.room}</p>
        `;
        checkoutSummary.appendChild(customerInfo);
        checkoutSummary.appendChild(document.createElement('hr'));
        checkoutSummary.appendChild(list);
    }

    // Submit order to checkout service
    function confirmOrder() {
        const customer = getFormValues();
        const orderPayload = {
            customer: {
                id: customer.student_id,
                name: customer.name,
                institute: customer.institute,
                phone: customer.phone,
                email: customer.email,
                room: customer.room,
            },
            items: cart,
        };
        fetch(ENDPOINTS.checkout, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(orderPayload),
        })
            .then(res => {
                if (!res.ok) throw new Error('Checkout failed');
                return res.json();
            })
            .then(() => {
                // Clear client-side cart and reload remote cart
                cart = [];
                loadCart();
                showSection('confirmation');
            })
            .catch(err => {
                console.error(err);
                alert('Failed to place order. Please try again.');
            });
    }

    // Button event handlers
    templateNextBtn.addEventListener('click', () => showSection('details'));
    document.getElementById('details-back-btn').addEventListener('click', () => showSection('select'));
    document.getElementById('preview-back-btn').addEventListener('click', () => showSection('details'));
    document.getElementById('cart-back-btn').addEventListener('click', () => showSection('preview'));
    document.getElementById('checkout-back-btn').addEventListener('click', () => showSection('cart'));

    document.getElementById('preview-btn').addEventListener('click', () => {
        // Ensure a template is selected and form is valid
        if (!selectedTemplate) {
            alert('Please select a template first.');
            return;
        }
        if (!detailsForm.reportValidity()) {
            return;
        }
        renderPreview();
        showSection('preview');
    });

    addCartBtn.addEventListener('click', () => {
        const values = getFormValues();
        const payload = {
            template_id: selectedTemplate.id,
            student_id: values.student_id,
            name: values.name,
            institute: values.institute,
            phone: values.phone,
            email: values.email,
            room: values.room,
        };
        fetch(ENDPOINTS.cart, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload),
        })
            .then(res => {
                if (!res.ok) throw new Error('Failed to add to cart');
                return res.json();
            })
            .then(() => {
                // After adding to cart reload list and go to cart page
                loadCart();
                showSection('cart');
            })
            .catch(err => {
                console.error(err);
                alert('Failed to add item to cart.');
            });
    });

    checkoutBtn.addEventListener('click', () => {
        renderCheckoutSummary();
        showSection('checkout');
    });

    confirmBtn.addEventListener('click', () => {
        confirmOrder();
    });

    // Kick off initial data loading
    loadTemplates();
    loadCart();
});
