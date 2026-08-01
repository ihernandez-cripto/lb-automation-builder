const API_BASE_URL = "http://127.0.0.1:8000";
let jsonGlobal = null;

async function ejecutarHistoriaUsuario(event) {
    // 🛑 DETENER LA RECARGA DE LA PÁGINA DE RAÍZ
    if (event) {
        event.preventDefault();
        event.stopPropagation();
    }

    const panel = document.getElementById('outputPanel');
    const btnDescarga = document.getElementById('downloadContainer');
    const inputStory = document.getElementById('userStoryInput');

    const textoStory = inputStory ? inputStory.value.trim() : "";
    if (!textoStory) {
        alert("Por favor ingrese un texto en la historia de usuario.");
        return false;
    }

    panel.textContent = "// Consultando backend y procesando con Gemini...";
    btnDescarga.style.display = 'none';

    try {
        const res = await fetch(`${API_BASE_URL}/api/process-user-story`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ user_story: textoStory })
        });

        const data = await res.json();

        if (!res.ok) {
            panel.textContent = "// ERROR DEVUELTO POR LA API:\n" + JSON.stringify(data, null, 4);
            return false;
        }

        // Asignar resultado y mostrar el panel de forma fija
        jsonGlobal = data.data || data.generated_config || data;
        panel.textContent = JSON.stringify(jsonGlobal, null, 4);
        
        // MOSTRAR BOTÓN DE DESCARGA
        btnDescarga.style.display = 'block';

    } catch (err) {
        panel.textContent = "// Error de conexión con FastAPI:\n" + err.message;
    }

    return false;
}

function descargarJSON() {
    if (!jsonGlobal) {
        alert("No hay ningún resultado generado aún.");
        return;
    }
    const dataStr = "data:text/json;charset=utf-8," + encodeURIComponent(JSON.stringify(jsonGlobal, null, 4));
    const dlAnchorElem = document.createElement('a');
    dlAnchorElem.setAttribute("href", dataStr);
    dlAnchorElem.setAttribute("download", "regla_configuracion_svlb.json");
    document.body.appendChild(dlAnchorElem);
    dlAnchorElem.click();
    dlAnchorElem.remove();
}