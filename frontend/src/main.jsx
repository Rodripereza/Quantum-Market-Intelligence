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
  Trash2,
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
      if (!activeToken) return;
      const headers = { Authorization: `Bearer ${activeToken}` };
      const [uRes, mRes, pRes, aRes] = await Promise.all([
        fetch(`${API}/api/user`, { headers }),
        fetch(`${API}/api/market`, { headers }),
        fetch(`${API}/api/portfolio`, { headers }),
        fetch(`${API}/api/ai/status`, { headers })
      ]);
      if ([uRes, mRes, pRes, aRes].some(r => r.status === 401)) {
        logout(false);
        return;
      }
      const [u, m, p, a] = await Promise.all([uRes.json(), mRes.json(), pRes.json(), aRes.json()]);
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

function Market({ market }) {
  return <Panel title="Market Overview" subtitle={market?.source || 'loading'}>{(market?.assets || []).map(a => <div className="row" key={a.ticker}><div><strong>{a.ticker}</strong><span>{a.name}</span></div><div><strong>{money(a.price)}</strong><em className={a.change_pct >= 0 ? 'pos' : 'neg'}>{pct(a.change_pct)}</em></div></div>)}</Panel>;
}

function Portfolio({ portfolio, form, setForm, savePosition, deletePosition, editingId, setEditingId, startEdit }) {
  const rows = portfolio?.positions || [];
  return (
    <>
      <div className="grid4">
        <Card title="Market Value" value={money(portfolio?.total_value)} subtitle="Current portfolio value" icon={<Wallet size={18} />} />
        <Card title="Cost Basis" value={money(portfolio?.total_cost)} subtitle="Invested capital" icon={<Database size={18} />} />
        <Card title="Total P/L" value={money(portfolio?.total_pl)} subtitle={pct(portfolio?.total_pl_pct)} icon={<Activity size={18} />} />
        <Card title="Largest Weight" value={pct(portfolio?.largest_position_weight)} subtitle="Concentration control" icon={<PieChart size={18} />} />
      </div>
      <Panel title={editingId ? 'Edit Position' : 'Add Position'} subtitle="Persistent SQLite portfolio engine">
        <form className="form portfolio-form" onSubmit={savePosition}>
          <input placeholder="Ticker" value={form.ticker} onChange={e => setForm({ ...form, ticker: e.target.value })} required />
          <input placeholder="Company" value={form.company} onChange={e => setForm({ ...form, company: e.target.value })} />
          <input placeholder="Sector" value={form.sector} onChange={e => setForm({ ...form, sector: e.target.value })} />
          <input placeholder="Quantity" value={form.quantity} onChange={e => setForm({ ...form, quantity: e.target.value })} required />
          <input placeholder="Average price" value={form.average_price} onChange={e => setForm({ ...form, average_price: e.target.value })} required />
          <input placeholder="Current price" value={form.current_price} onChange={e => setForm({ ...form, current_price: e.target.value })} />
          <input className="wide-input" placeholder="Notes" value={form.notes} onChange={e => setForm({ ...form, notes: e.target.value })} />
          <button>{editingId ? 'Save changes' : 'Add position'}</button>
          {editingId && <button type="button" className="secondary-button" onClick={() => { setEditingId(null); setForm({ ticker: '', company: '', sector: '', quantity: '', average_price: '', current_price: '', notes: '' }); }}>Cancel</button>}
        </form>
      </Panel>
      <Panel title="Portfolio Positions" subtitle={`${rows.length} positions · editable engine`}>
        <div className="table-head"><span>Ticker</span><span>Company</span><span>Sector</span><span>Qty</span><span>Avg</span><span>Price</span><span>Value</span><span>P/L</span><span>Weight</span><span>Actions</span></div>
        <div className="table">{rows.map(p => <div className="trow portfolio-row" key={p.id}><b>{p.ticker}</b><span>{p.company}</span><span>{p.sector}</span><span>{p.quantity}</span><span>{money(p.average_price)}</span><span>{money(p.current_price)}</span><span>{money(p.value)}</span><span className={p.pl >= 0 ? 'pos' : 'neg'}>{money(p.pl)} · {pct(p.pl_pct)}</span><span>{pct(p.weight)}</span><div className="row-actions"><button onClick={() => startEdit(p)}>Edit</button><button onClick={() => deletePosition(p.id)}><Trash2 size={14}/></button></div></div>)}</div>
      </Panel>
      <Panel title="Sector Allocation" subtitle="Exposure distribution">
        <div className="metric-list">{(portfolio?.sector_allocation || []).map(s => <div key={s.sector}><strong>{s.sector}</strong><span>{money(s.value)} · {pct(s.weight)}</span></div>)}</div>
      </Panel>
    </>
  );
}

function AI({ ai }) {
  return <Panel title="AI Intelligence" subtitle={ai?.status || 'loading'}><p>{ai?.message}</p><div className="chips">{(ai?.modules || []).map(m => <span key={m}>{m}</span>)}</div></Panel>;
}

function DataPage({ portfolio, market }) {
  return <Panel title="Data Layer" subtitle="SQLite operational foundation"><div className="metric-list"><div><strong>Database</strong><span>backend/data/qmi_foundation.db</span></div><div><strong>Portfolio records</strong><span>{portfolio?.positions?.length ?? '--'}</span></div><div><strong>Sector groups</strong><span>{portfolio?.sector_allocation?.length ?? '--'}</span></div><div><strong>Market assets</strong><span>{market?.assets?.length ?? '--'}</span></div></div></Panel>;
}

function RiskPage({ portfolio }) {
  const concentration = Math.max(...(portfolio?.positions || []).map(p => p.weight), 0);
  return <Panel title="Risk Layer" subtitle="Authenticated risk workspace"><div className="grid3"><Card title="Max Position Weight" value={pct(concentration)} subtitle="Concentration signal" icon={<Gauge size={18}/>} /><Card title="Open Positions" value={portfolio?.positions?.length ?? '--'} subtitle="Portfolio breadth" icon={<PieChart size={18}/>} /><Card title="Risk Engine" value="Prepared" subtitle="Future scoring module" icon={<Shield size={18}/>} /></div></Panel>;
}

function SettingsPage({ apiOk, user }) {
  return <Panel title="Settings" subtitle="Local environment"><div className="metric-list"><div><strong>Frontend</strong><span>React + Vite</span></div><div><strong>Backend</strong><span>FastAPI + SQLite</span></div><div><strong>Python target</strong><span>3.12.x</span></div><div><strong>API status</strong><span>{apiOk ? 'Online' : 'Offline'}</span></div><div><strong>User</strong><span>{user?.name || 'Rodri'}</span></div><div><strong>Email</strong><span>{user?.email || 'rodripereza8@gmail.com'}</span></div><div><strong>Workspace</strong><span>{user?.workspace || 'Quantum Market Intelligence'}</span></div></div></Panel>;
}

createRoot(document.getElementById('root')).render(<App />);
