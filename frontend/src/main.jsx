import React, { useEffect, useMemo, useState } from 'react';
import { createRoot } from 'react-dom/client';
import {
  Activity,
  Bell,
  Brain,
  ChevronRight,
  Database,
  Gauge,
  Home,
  LineChart,
  Menu,
  PieChart,
  Search,
  Settings,
  Shield,
  User,
  Wallet,
  X
} from 'lucide-react';
import './style.css';
import Panel from "./components/ui/Panel";
import Card from "./components/ui/Card";
import Sidebar from "./components/layout/Sidebar";
import Topbar from "./components/layout/Topbar";
import PageShell from "./components/layout/PageShell";
import Overview from "./pages/Overview";
import Portfolio from "./pages/Portfolio";
import Market from "./pages/Market";
import AI from "./pages/AI";
import RiskPage from "./pages/RiskPage";
import DataPage from "./pages/DataPage";
import SettingsPage from "./pages/SettingsPage";
import { getUser } from "./services/authService";
import { getMarket } from "./services/marketService";
import { getPortfolio } from "./services/portfolioService";
import { getAIStatus } from "./services/aiService";

const API = 'http://127.0.0.1:8000';

const NAV_SECTIONS = [
  {
    title: 'Core',
    items: [
      { id: 'overview', label: 'Overview', icon: Home, description: 'Executive control center' },
      { id: 'market', label: 'Market', icon: LineChart, description: 'Market intelligence' },
      { id: 'portfolio', label: 'Portfolio', icon: Wallet, description: 'Portfolio engine' }
    ]
  },
  {
    title: 'Intelligence',
    items: [
      { id: 'ai', label: 'AI Intelligence', icon: Brain, description: 'Prediction layer' },
      { id: 'risk', label: 'Risk', icon: Shield, description: 'Risk monitoring' },
      { id: 'data', label: 'Data', icon: Database, description: 'Data architecture' }
    ]
  },
  {
    title: 'System',
    items: [
      { id: 'settings', label: 'Settings', icon: Settings, description: 'Environment settings' }
    ]
  }
];

const ALL_NAV = NAV_SECTIONS.flatMap(section => section.items);

function money(n, currency = 'USD') {
  if (n === null || n === undefined || Number.isNaN(Number(n))) return '--';
  return new Intl.NumberFormat('en-US', { style: 'currency', currency, maximumFractionDigits: 2 }).format(n);
}

function pct(n) {
  if (n === null || n === undefined || Number.isNaN(Number(n))) return '--';
  return `${Number(n || 0).toFixed(2)}%`;
}

function getInitialPage() {
  const hash = window.location.hash.replace('#/', '') || 'overview';
  return ALL_NAV.some(item => item.id === hash) ? hash : 'overview';
}

function App() {
  const [page, setPage] = useState(getInitialPage());
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [apiOk, setApiOk] = useState(false);
  const [token, setToken] = useState(localStorage.getItem('qmi_token') || '');
  const [authError, setAuthError] = useState('');
  const [user, setUser] = useState(null);
  const [market, setMarket] = useState(null);
  const [portfolio, setPortfolio] = useState(null);
  const [ai, setAi] = useState(null);
  const [form, setForm] = useState({ ticker: '', company: '', sector: '', quantity: '', average_price: '', current_price: '', notes: '' });
  const [editingId, setEditingId] = useState(null);

  const active = ALL_NAV.find(item => item.id === page) || ALL_NAV[0];

  function navigate(nextPage) {
    setPage(nextPage);
    window.location.hash = `/${nextPage}`;
    setSidebarOpen(false);
  }

  async function load(activeToken = token) {
    try {
        const health = await fetch(`${API}/health`);
        setApiOk(health.ok);

        if (!activeToken) {
            return;
        }
      let u;
      let m;
      let p;
      let a;

      try {
        [u, m, p, a] = await Promise.all([
          getUser(activeToken),
          getMarket(activeToken),
          getPortfolio(activeToken),
          getAIStatus(activeToken)
        ]);
    } catch (error) {
    if (error.status === 401) {
        logout(false);
        return;
    }

    throw error;
    }
      setUser(u);
      setMarket(m);
      setPortfolio(p);
      setAi(a);
    } catch (error) {
      setApiOk(false);
    }
  }

  useEffect(() => {
    load(token);
    const onHashChange = () => setPage(getInitialPage());
    window.addEventListener('hashchange', onHashChange);
    return () => window.removeEventListener('hashchange', onHashChange);
  }, [token]);

  const allocation = useMemo(
    () => (portfolio?.positions || []).map(p => ({ ticker: p.ticker, value: p.value, weight: p.weight })),
    [portfolio]
  );
  const sectorAllocation = useMemo(() => portfolio?.sector_allocation || [], [portfolio]);

  const trend = [
    { month: 'Jan', value: 42 },
    { month: 'Feb', value: 47 },
    { month: 'Mar', value: 46 },
    { month: 'Apr', value: 55 },
    { month: 'May', value: 63 },
    { month: 'Jun', value: 72 }
  ];

  async function savePosition(e) {
    e.preventDefault();
    const payload = {
      ticker: form.ticker,
      company: form.company || form.ticker,
      sector: form.sector || 'Unclassified',
      quantity: Number(form.quantity),
      average_price: Number(form.average_price),
      current_price: Number(form.current_price || form.average_price),
      currency: 'USD',
      notes: form.notes || ''
    };
    const url = editingId ? `${API}/api/portfolio/positions/${editingId}` : `${API}/api/portfolio/positions`;
    const method = editingId ? 'PUT' : 'POST';
    const response = await fetch(url, {
      method,
      headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
      body: JSON.stringify(payload)
    });
    const data = await response.json();
    if (data.portfolio) setPortfolio(data.portfolio);
    setEditingId(null);
    setForm({ ticker: '', company: '', sector: '', quantity: '', average_price: '', current_price: '', notes: '' });
  }

  function startEdit(position) {
    setEditingId(position.id);
    setForm({
      ticker: position.ticker,
      company: position.company,
      sector: position.sector || '',
      quantity: String(position.quantity),
      average_price: String(position.average_price),
      current_price: String(position.current_price),
      notes: position.notes || ''
    });
    navigate('portfolio');
  }

  async function deletePosition(id) {
    const response = await fetch(`${API}/api/portfolio/positions/${id}`, { method: 'DELETE', headers: { Authorization: `Bearer ${token}` } });
    const data = await response.json();
    if (data.portfolio) setPortfolio(data.portfolio); else load();
  }


  async function login(email, password) {
    setAuthError('');
    try {
      const response = await fetch(`${API}/api/auth/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password })
      });
      if (!response.ok) {
        setAuthError('Invalid email or password');
        return;
      }
      const data = await response.json();
      localStorage.setItem('qmi_token', data.access_token);
      setToken(data.access_token);
      setUser(data.user);
    } catch (error) {
      setAuthError('Backend authentication service unavailable');
    }
  }

  async function logout(callApi = true) {
    if (callApi && token) {
      await fetch(`${API}/api/auth/logout`, { method: 'POST', headers: { Authorization: `Bearer ${token}` } }).catch(() => null);
    }
    localStorage.removeItem('qmi_token');
    setToken('');
    setUser(null);
    setMarket(null);
    setPortfolio(null);
    setAi(null);
  }

  if (!token) {
    return <LoginScreen apiOk={apiOk} authError={authError} login={login} />;
  }

  return (
    <div className="app">
      <Sidebar
        page={page}
        navigate={navigate}
        open={sidebarOpen}
        close={() => setSidebarOpen(false)}
        navSections={NAV_SECTIONS}
      />
      <main className="main">
        <Topbar
          active={active}
          apiOk={apiOk}
          user={user}
          logout={logout}
          openSidebar={() => setSidebarOpen(true)}
        />
        <PageShell active={active}>
          {page === 'overview' && <Overview portfolio={portfolio} market={market} ai={ai} trend={trend} allocation={allocation} sectorAllocation={sectorAllocation} navigate={navigate} />}
          {page === 'market' && <Market market={market} />}
          {page === 'portfolio' && <Portfolio portfolio={portfolio} form={form} setForm={setForm} savePosition={savePosition} deletePosition={deletePosition} editingId={editingId} setEditingId={setEditingId} startEdit={startEdit} />}
          {page === 'ai' && <AI ai={ai} />}
          {page === 'data' && <DataPage portfolio={portfolio} market={market} />}
          {page === 'risk' && <RiskPage portfolio={portfolio} />}
          {page === 'settings' && <SettingsPage apiOk={apiOk} user={user} />}
        </PageShell>
      </main>
    </div>
  );
}

function LoginScreen({ apiOk, authError, login }) {
  const [email, setEmail] = useState('rodripereza8@gmail.com');
  const [password, setPassword] = useState('qmi123');
  return (
    <div className="login-screen">
      <div className="login-card">
        <div className="logo">QMI</div>
        <div className="eyebrow">QUANTUM MARKET INTELLIGENCE · FOUNDATION v1.3</div>
        <h1>Secure Workspace Access</h1>
        <p>Authentication layer active. Sign in to access the institutional dashboard.</p>
        <form onSubmit={(e) => { e.preventDefault(); login(email, password); }} className="login-form">
          <label>Email</label>
          <input value={email} onChange={e => setEmail(e.target.value)} />
          <label>Password</label>
          <input type="password" value={password} onChange={e => setPassword(e.target.value)} />
          {authError && <div className="auth-error">{authError}</div>}
          <button>Enter QMI</button>
        </form>
        <div className="login-footer">
          <span className={apiOk ? 'ok' : 'bad'}>{apiOk ? 'API OK' : 'API OFFLINE'}</span>
          <span>Default user: rodripereza8@gmail.com / qmi123</span>
        </div>
      </div>
    </div>
  );
}

createRoot(document.getElementById('root')).render(<App />);
