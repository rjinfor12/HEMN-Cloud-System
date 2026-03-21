/**
 * HEMN SYSTEM PROMOTIONAL WALKTHROUGH SCRIPT
 * This script automates the UI to showcase features while providing 
 * voiceover (speechSynthesis) and visual subtitles.
 */

async function startWalkthrough() {
    // 1. Setup - Mock Login
    localStorage.setItem("hemn_token", "promotional-token");
    localStorage.setItem("hemn_user", JSON.stringify({ name: "Demo User", role: "Elite Admin", balance: 500.00 }));
    location.reload(); // Reload to apply login state
}

// Check if we are already "logged in" by the script's first run
if (localStorage.getItem("hemn_token") === "promotional-token" && !window.walkthroughInProgress) {
    window.walkthroughInProgress = true;
    runDemo();
} else if (!window.walkthroughInProgress) {
    startWalkthrough();
}

async function runDemo() {
    console.log("Starting HEMN SYSTEM Walkthrough...");
    
    const synth = window.speechSynthesis;
    const voice = synth.getVoices().find(v => v.lang.startsWith('pt')) || synth.getVoices()[0];

    // Create Subtitle Overlay
    const subContainer = document.createElement('div');
    subContainer.style.cssText = `
        position: fixed; bottom: 40px; left: 50%; transform: translateX(-50%);
        background: rgba(0, 0, 0, 0.85); color: #fff; padding: 15px 30px;
        border-radius: 50px; font-family: 'Inter', sans-serif; font-size: 1.2rem;
        z-index: 10000; backdrop-filter: blur(10px); border: 1px solid rgba(255,255,255,0.1);
        box-shadow: 0 10px 30px rgba(0,0,0,0.5); opacity: 0; transition: opacity 0.5s;
        text-align: center; max-width: 80%;
    `;
    document.body.appendChild(subContainer);

    function showSubtitle(text, duration = 4000) {
        subContainer.innerText = text;
        subContainer.style.opacity = '1';
        
        const msg = new SpeechSynthesisUtterance(text);
        msg.voice = voice;
        msg.lang = 'pt-BR';
        msg.rate = 1.0;
        synth.speak(msg);

        return new Promise(resolve => setTimeout(() => {
            subContainer.style.opacity = '0';
            setTimeout(resolve, 500);
        }, duration));
    }

    // --- SCENE 1: Intro ---
    await new Promise(r => setTimeout(r, 1000)); // Wait for UI load
    await showSubtitle("Bem-vindo ao HEMN SYSTEM: A nova era da inteligência de dados.");

    // --- SCENE 2: Home Dashboard ---
    await showSubtitle("Um dashboard completo para monitorar sua operação em tempo real.");
    
    // --- SCENE 3: Unitary Search ---
    document.getElementById('nav-manual').click();
    await new Promise(r => setTimeout(r, 1000));
    await showSubtitle("Realize consultas unitárias ultra-rápidas em nossa base de alta performance.");
    
    const nameInput = document.getElementById('manual-name');
    nameInput.value = "JOÃO DA SILVA";
    await new Promise(r => setTimeout(r, 1000));
    await showSubtitle("Encontre CPF, CNPJ e histórico com um clique.");

    // --- SCENE 4: Data Extraction ---
    document.getElementById('nav-extract').click();
    await new Promise(r => setTimeout(r, 1000));
    await showSubtitle("Extração massiva inteligente com filtros avançados de localização e CNAE.");
    
    // Show some filters
    document.getElementById('extract-uf').value = "SP";
    document.getElementById('extract-cidade').value = "SÃO PAULO";
    await new Promise(r => setTimeout(r, 1000));
    await showSubtitle("Gere leads qualificados segmentados por operadora e situação cadastral.");

    // --- SCENE 5: Carrier Query ---
    document.getElementById('nav-carrier').click();
    await new Promise(r => setTimeout(r, 1000));
    await showSubtitle("Identifique portabilidade e operadoras com precisão cirúrgica.");

    // --- SCENE 6: Unification & Splitting ---
    document.getElementById('nav-unify').click();
    await new Promise(r => setTimeout(r, 1000));
    await showSubtitle("Unifique bases gigantes e deduplique registros em segundos.");

    // --- SCENE 7: Dashboard ---
    document.getElementById('nav-dashboard').click();
    await new Promise(r => setTimeout(r, 1000));
    await showSubtitle("Controle total de créditos, consumos e estatísticas de uso.");

    // --- SCENE 8: Closing ---
    app.showModule('inicio', document.getElementById('nav-inicio'));
    await new Promise(r => setTimeout(r, 1000));
    await showSubtitle("HEMN SYSTEM: Potencialize sua empresa com o poder dos dados. Comece agora!");

    subContainer.remove();
    window.walkthroughFinished = true;
    console.log("Walkthrough Finished.");
}
