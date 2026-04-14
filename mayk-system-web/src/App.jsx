import React, { useState, useEffect } from 'react';
import './App.css';

// Mock Data (Ported from Desktop Logic)
const INITIAL_SALES = [
  { id: 1, nome_cliente: 'Exemplo de Cliente', valor_manual: 1500.00, status_atual_venda: 6, consultor: 'Admin' },
  { id: 2, nome_cliente: 'Maria Oliveira', valor_manual: 2200.50, status_atual_venda: 1, consultor: 'Admin' },
  { id: 3, nome_cliente: 'João Souza', valor_manual: 900.00, status_atual_venda: 2, consultor: 'Admin' },
];

const STATUS_MAP = {
  6: { name: "Triagem Inicial", badge: "badge-blue" },
  1: { name: "Aprovada", badge: "badge-green" },
  2: { name: "Instalada", badge: "badge-purple" },
  3: { name: "Cancelada / Recusada", badge: "badge-red" },
};

function App() {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [user, setUser] = useState(null);
  const [activeTab, setActiveTab] = useState('dashboard');
  const [sales, setSales] = useState(INITIAL_SALES);
  
  // Chamados/Tecnicos State (Recuperado)
  const [tickets, setTickets] = useState([
    { id: 101, machine: 'MAQ-01', floor: 2, tech: 'Carlos Silva', status: 'Em Andamento', cat: 'Falha de Conexão', time: '10:15', user: 'Operador A', text: 'Sem sinal no CLP.' },
    { id: 102, machine: 'MAQ-05', floor: 4, tech: 'Roberto Junior', status: 'Aberto', cat: 'Elétrica', time: '11:20', user: 'Manager 2', text: 'Disjuntor disparando.' }
  ]);

  const [tecnicos, setTecnicos] = useState([
    { name: 'Carlos Silva', xp: 1250, status: 'Atendendo', color: '#3b82f6', floor: 2, direction: 'Subindo' },
    { name: 'Roberto Junior', xp: 980, status: 'Disponível', color: '#10b981', floor: 0, direction: 'Aguardando' },
    { name: 'André Lima', xp: 750, status: 'Almoço', color: '#f59e0b', floor: 0, direction: 'Pendente' }
  ]);

  const handleReabrir = (ticket) => {
    // Penalidade de -75 XP ao reabrir chamado concluído
    const updatedTecs = tecnicos.map(t => 
      t.name === ticket.tech ? { ...t, xp: t.xp - 75 } : t
    );
    setTecnicos(updatedTecs);
    
    // Reatribuir para outro técnico usando Round Robin
    const nextTech = updatedTecs.filter(t => t.status === 'Disponível')[0]?.name || updatedTecs[0].name;
    
    const updatedTickets = tickets.map(t => 
      t.id === ticket.id ? { ...t, status: 'Aberto', tech: nextTech } : t
    );
    setTickets(updatedTickets);
  };
  
  // Login Logic
  const handleLogin = (e) => {
    e.preventDefault();
    const username = e.target.username.value;
    const password = e.target.password.value;
    
    if (username === 'admin' && password === 'admin') {
      setIsAuthenticated(true);
      setUser({ name: 'Administrador', role: 'Diretor' });
    } else {
      alert('Credenciais Inválidas');
    }
  };

  if (!isAuthenticated) {
    return (
      <div style={{ display: 'flex', height: '100vh', alignItems: 'center', justifyContent: 'center', background: 'var(--bg)' }}>
        <div className="glass-card" style={{ width: '100%', maxWidth: '400px', textAlign: 'center' }}>
          <h1 className="brand-name" style={{ fontSize: '32px', marginBottom: '8px' }}>MAYK SYSTEM</h1>
          <p className="page-subtitle" style={{ marginBottom: '32px' }}>Acesse seu CRM Local</p>
          
          <form onSubmit={handleLogin} style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
            <div className="form-group" style={{ textAlign: 'left' }}>
              <label>Usuário</label>
              <input name="username" type="text" placeholder="admin" required />
            </div>
            <div className="form-group" style={{ textAlign: 'left' }}>
              <label>Senha</label>
              <input name="password" type="password" placeholder="••••••••" required />
            </div>
            <button type="submit" className="btn-primary" style={{ width: '100%', justifyContent: 'center', height: '48px', marginTop: '12px' }}>
              Entrar no Sistema
            </button>
            <p className="user-role" style={{ marginTop: '12px' }}>Use admin / admin</p>
          </form>
        </div>
      </div>
    );
  }

  const totalValue = sales.reduce((acc, curr) => acc + curr.valor_manual, 0);

  return (
    <div id="app">
      {/* Sidebar */}
      <aside className="sidebar">
        <div className="logo-container">
          <div className="avatar">M</div>
          <span className="brand-name">MAYK SYSTEM</span>
        </div>
        
        <nav className="nav-menu">
          <p className="nav-label">Menu Principal</p>
          <button 
            className={`nav-link ${activeTab === 'dashboard' ? 'active' : ''}`}
            onClick={() => setActiveTab('dashboard')}
          >
            <span className="icon">📊</span> Dashboard
          </button>
          <button 
            className={`nav-link ${activeTab === 'kanban' ? 'active' : ''}`}
            onClick={() => setActiveTab('kanban')}
          >
            <span className="icon">📋</span> Kanban
          </button>
          <button 
            className={`nav-link ${activeTab === 'clientes' ? 'active' : ''}`}
            onClick={() => setActiveTab('clientes')}
          >
            <span className="icon">👥</span> Clientes
          </button>
          <button 
            className={`nav-link ${activeTab === 'tickets' ? 'active' : ''}`}
            onClick={() => setActiveTab('tickets')}
          >
            <span className="icon">🛠️</span> Chamados
          </button>
          <button 
            className={`nav-link ${activeTab === 'radar' ? 'active' : ''}`}
            onClick={() => setActiveTab('radar')}
          >
            <span className="icon">🛰️</span> Radar
          </button>
          <button 
            className={`nav-link ${activeTab === 'ranking' ? 'active' : ''}`}
            onClick={() => setActiveTab('ranking')}
          >
            <span className="icon">🏆</span> Ranking
          </button>
          
          <p className="nav-label">Configurações</p>
          <button className="nav-link">
            <span className="icon">⚙️</span> Ajustes
          </button>
        </nav>

        <div className="user-profile">
          <div className="avatar">{user.name[0]}</div>
          <div className="user-info">
            <span className="user-name">{user.name}</span>
            <span className="user-role">{user.role}</span>
          </div>
        </div>
      </aside>

      {/* Main Content */}
      <main className="content-area">
        <header className="top-bar">
          <div className="search-bar">
            <span className="search-icon">🔍</span>
            <input type="text" placeholder="Buscar cliente ou oportunidade..." />
          </div>
          <div className="header-tools">
            <button className="icon-btn">🔔</button>
            <button className="btn-primary" onClick={() => setActiveTab('kanban')}>
              + Nova Venda
            </button>
          </div>
        </header>

        <div className="page-container">
          {activeTab === 'dashboard' && (
            <div key="dashboard">
              <div className="welcome-header">
                <h1>Bem-vindo, {user.name.split(' ')[0]}!</h1>
                <p>Aqui está o resumo da sua operação hoje.</p>
              </div>

              <div className="stats-grid">
                <div className="glass-card stat-card">
                  <span className="stat-label">Volume Financeiro</span>
                  <span className="stat-value">R$ {totalValue.toLocaleString('pt-BR', { minimumFractionDigits: 2 })}</span>
                  <span className="stat-trend up">↑ 12% este mês</span>
                </div>
                <div className="glass-card stat-card">
                  <span className="stat-label">Total de Vendas</span>
                  <span className="stat-value">{sales.length}</span>
                  <span className="stat-trend up">↑ 5 novas hoje</span>
                </div>
                <div className="glass-card stat-card">
                  <span className="stat-label">Ticket Médio</span>
                  <span className="stat-value">R$ {(totalValue / sales.length).toLocaleString('pt-BR', { minimumFractionDigits: 2 })}</span>
                </div>
              </div>

              <div className="glass-card">
                <h3 style={{ marginBottom: '20px' }}>Oportunidades Recentes</h3>
                <div className="table-wrapper">
                  <table className="data-table">
                    <thead>
                      <tr>
                        <th>Cliente</th>
                        <th>Valor</th>
                        <th>Status</th>
                        <th>Ação</th>
                      </tr>
                    </thead>
                    <tbody>
                      {sales.map(s => (
                        <tr key={s.id}>
                          <td><strong>{s.nome_cliente}</strong></td>
                          <td>R$ {s.valor_manual.toFixed(2)}</td>
                          <td>
                            <span className={`badge ${STATUS_MAP[s.status_atual_venda]?.badge}`}>
                              {STATUS_MAP[s.status_atual_venda]?.name}
                            </span>
                          </td>
                          <td><button className="btn-secondary" style={{ padding: '4px 12px' }}>Ver</button></td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            </div>
          )}

          {activeTab === 'kanban' && (
            <div key="kanban">
              <div className="page-header">
                <h1 className="page-title">Funil de Vendas</h1>
                <p className="page-subtitle">Gerencie suas oportunidades em tempo real</p>
              </div>
              
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '16px', height: 'calc(100vh - 250px)' }}>
                {[6, 1, 2, 3].map(statusId => (
                  <div key={statusId} className="glass-card" style={{ padding: '12px', display: 'flex', flexDirection: 'column', gap: '12px', background: 'rgba(255,255,255,0.02)' }}>
                    <h3 style={{ fontSize: '14px', textTransform: 'uppercase', color: 'var(--text-2)', borderBottom: '1px solid var(--border)', paddingBottom: '8px' }}>
                      {STATUS_MAP[statusId].name}
                    </h3>
                    <div style={{ flex: 1, overflowY: 'auto' }}>
                      {sales.filter(s => s.status_atual_venda === statusId).map(s => (
                        <div key={s.id} className="glass-card" style={{ marginBottom: '12px', padding: '16px', background: 'var(--bg-card)' }}>
                          <p style={{ fontWeight: '600', marginBottom: '8px' }}>{s.nome_cliente}</p>
                          <p style={{ fontSize: '12px', color: 'var(--text-2)' }}>R$ {s.valor_manual.toFixed(2)}</p>
                        </div>
                      ))}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {activeTab === 'clientes' && (
            <div className="glass-card" style={{ textAlign: 'center', padding: '80px' }}>
              <span className="icon" style={{ fontSize: '48px' }}>🚧</span>
              <h2>Módulo Clientes</h2>
              <p>Esta funcionalidade está sendo portada do sistema desktop.</p>
            </div>
          )}

          {activeTab === 'tickets' && (
            <div key="tickets">
              <div className="page-header">
                <h1 className="page-title">Gestão de Chamados</h1>
                <p className="page-subtitle">Roteamento e atendimento técnico</p>
              </div>
              <div className="tickets-list" style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
                {tickets.map(t => (
                  <div key={t.id} className="glass-card" style={{ padding: '20px', borderLeft: `4px solid ${t.status === 'Aberto' ? '#ef4444' : '#3b82f6'}` }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                      <div>
                        <span style={{ fontSize: '12px', color: 'var(--text-3)' }}>#{t.id} • {t.machine} (Andar {t.floor})</span>
                        <h3 style={{ margin: '4px 0' }}>{t.cat}</h3>
                      </div>
                      <span className={`badge ${t.status === 'Aberto' ? 'badge-red' : 'badge-blue'}`}>{t.status}</span>
                    </div>
                    <div style={{ marginTop: '12px', display: 'flex', gap: '20px', fontSize: '13px', color: 'var(--text-2)' }}>
                      <span>👤 {t.tech}</span>
                      <span>🕒 {t.time}</span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {activeTab === 'radar' && (
            <div key="radar">
              <div className="page-header">
                <h1 className="page-title">Radar de Técnicos</h1>
                <p className="page-subtitle">Acompanhamento vertical em tempo real</p>
              </div>
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: '20px' }}>
                {tecnicos.map(tec => (
                  <div key={tec.name} className="glass-card" style={{ padding: '20px' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '15px' }}>
                      <div className="avatar" style={{ background: tec.color }}>{tec.name[0]}</div>
                      <div>
                        <p style={{ fontWeight: '800' }}>{tec.name}</p>
                        <p style={{ fontSize: '11px', color: 'var(--text-3)' }}>{tec.status}</p>
                      </div>
                      <div style={{ marginLeft: 'auto', textAlign: 'right' }}>
                        <p style={{ fontSize: '14px', fontWeight: '800', color: 'var(--accent-blue)' }}>{tec.xp} XP</p>
                      </div>
                    </div>
                    <div style={{ marginTop: '15px', background: 'rgba(255,255,255,0.03)', padding: '12px', borderRadius: '8px' }}>
                      <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '12px', marginBottom: '8px' }}>
                        <span>{tec.direction}</span>
                        <span>Andar {tec.floor}</span>
                      </div>
                      <div style={{ height: '4px', background: 'var(--border)', borderRadius: '2px', overflow: 'hidden' }}>
                        <div style={{ height: '100%', width: tec.status === 'Atendendo' ? '70%' : '0%', background: 'var(--g-primary)', transition: 'width 1s ease' }}></div>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {activeTab === 'ranking' && (
            <div key="ranking">
              <div className="page-header">
                <h1 className="page-title">Ranking de Performance</h1>
                <p className="page-subtitle">Líderes de atendimento e qualidade</p>
              </div>
              <div className="glass-card" style={{ padding: '0' }}>
                {tecnicos.sort((a,b) => b.xp - a.xp).map((tec, idx) => (
                  <div key={tec.name} style={{ display: 'flex', alignItems: 'center', padding: '15px 25px', borderBottom: idx === tecnicos.length - 1 ? 'none' : '1px solid var(--border)' }}>
                    <span style={{ width: '40px', fontWeight: '800', color: idx === 0 ? '#f59e0b' : 'var(--text-3)' }}>#{idx + 1}</span>
                    <div className="avatar" style={{ background: tec.color, width: '32px', height: '32px', marginRight: '15px' }}>{tec.name[0]}</div>
                    <span style={{ flex: 1, fontWeight: '600' }}>{tec.name}</span>
                    <span style={{ fontWeight: '800' }}>{tec.xp} XP</span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </main>
    </div>
  );
}

export default App;