function toggleCustomHeader(value) {
    const customGroup = document.getElementById('customHeaderGroup');
    const customInput = document.getElementById('customMhdr');
    if (value === 'custom') {
        customGroup.style.display = 'block';
        customInput.required = true;
    } else {
        customGroup.style.display = 'none';
        customInput.required = false;
    }
}

function showOutput(text) {
    const outputPanel = document.getElementById('outputPanel');
    outputPanel.style.display = 'block';
    outputPanel.textContent = text;
}

function formatErrorDetail(data, fallback) {
    if (!data) return fallback;
    if (typeof data.detail === 'object') return JSON.stringify(data.detail, null, 2);
    if (data.detail) return String(data.detail);
    return fallback;
}

document.addEventListener('DOMContentLoaded', () => {
    const mhdrPreset = document.getElementById('mhdrPreset');
    if (mhdrPreset) {
        mhdrPreset.addEventListener('change', (e) => toggleCustomHeader(e.target.value));
    }

    const form = document.getElementById('slbForm');
    if (!form) return;

    form.addEventListener('submit', async function (e) {
        e.preventDefault();

        const submitBtn = form.querySelector('button[type="submit"]');
        if (submitBtn) submitBtn.disabled = true;

        showOutput("// Enviando datos al flujo de agentes backend...");

        const payload = {
            ip: document.getElementById('ipAddress').value.trim(),
            port: document.getElementById('portConfig').value.trim(),
            range_count: document.getElementById('portRangeCount').value.trim(),
            mhdr_preset: document.getElementById('mhdrPreset').value,
            custom_mhdr: (document.getElementById('customMhdr') || {}).value ? document.getElementById('customMhdr').value.trim() : ""
        };

        // Simple client-side validation
        if (payload.range_count && isNaN(Number(payload.range_count))) {
            showOutput("// ERROR: " + "'Cantidad en Rango' debe ser numérico.");
            if (submitBtn) submitBtn.disabled = false;
            return;
        }

        try {
            // Definir API_BASE según el entorno:
            // - Si la página se abre vía file:// se asume desarrollo local con backend en http://127.0.0.1:8000
            // - En cualquier otro caso se usa ruta relativa (útil al servir la app desde el mismo host)
            const API_BASE = (location.protocol === 'file:') ? 'http://127.0.0.1:8000' : '';

            const response = await fetch(`${API_BASE}/api/generate-config`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(payload)
            });

            const text = await response.text();
            let data = null;
            try { data = text ? JSON.parse(text) : null; } catch (err) { data = null; }

            if (!response.ok) {
                const errMsg = formatErrorDetail(data, text || 'Error desconocido del servidor');
                showOutput(`// ERROR DE VALIDACIÓN:\n${errMsg}`);
                return;
            }

            const result = data && data.generated_config ? data.generated_config : data;
            showOutput("// Resultado Procesado por Agentes SVLB:\n" + (result ? JSON.stringify(result, null, 4) : text));

        } catch (error) {
            showOutput("// Error de conexión con el backend multiagente.\n" +
                "Asegúrate de que el backend esté corriendo y que la ruta /api/generate-config sea accesible.");
        } finally {
            if (submitBtn) submitBtn.disabled = false;
        }
    });
});
