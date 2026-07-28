import { useEffect, useMemo, useState } from "react";

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
  X,
} from "lucide-react";

import Panel from "./components/ui/Panel";
import Card from "./components/ui/Card";
import Sidebar from "./components/layout/Sidebar";
import Topbar from "./components/layout/Topbar";
import PageShell from "./components/layout/PageShell";

import Dashboard from "./pages/Dashboard";
import Portfolio from "./pages/Portfolio";
import Market from "./pages/Market";
import AI from "./pages/AI";
import RiskPage from "./pages/RiskPage";
import DataPage from "./pages/DataPage";
import SettingsPage from "./pages/SettingsPage";
import AIInvestmentAdvisor from "./pages/AIInvestmentAdvisor";

import { getHealth } from "./services/systemService";

import {
  getUser,
  login as loginService,
  logout as logoutService,
} from "./services/authService";

import { getMarket } from "./services/marketService";

import {
  getPortfolio,
  createPosition,
  updatePosition,
  deletePosition as deletePositionService,
} from "./services/portfolioService";

import { getAIStatus } from "./services/aiService";

const NAV_SECTIONS = [
  {
    title: "Core",
    items: [
      {
        id: "overview",
        label: "Overview",
        icon: Home,
        description: "Executive control center",
      },
      {
        id: "market",
        label: "Market",
        icon: LineChart,
        description: "Market intelligence",
      },
      {
        id: "portfolio",
        label: "Portfolio",
        icon: Wallet,
        description: "Portfolio engine",
      },
    ],
  },
  {
    title: "Intelligence",
    items: [
      {
        id: "ai",
        label: "AI Intelligence",
        icon: Brain,
        description: "Prediction layer",
      },
      {
        id: "ai-advisor",
        label: "AI Advisor",
        icon: Brain,
        description: "Multi-factor recommendation",
      },
      {
        id: "risk",
        label: "Risk",
        icon: Shield,
        description: "Risk monitoring",
      },
      {
        id: "data",
        label: "Data",
        icon: Database,
        description: "Data architecture",
      },
    ],
  },
  {
    title: "System",
    items: [
      {
        id: "settings",
        label: "Settings",
        icon: Settings,
        description: "Environment settings",
      },
    ],
  },
];

const ALL_NAV = NAV_SECTIONS.flatMap((section) => section.items);

function money(number, currency = "USD") {
  if (
    number === null ||
    number === undefined ||
    Number.isNaN(Number(number))
  ) {
    return "--";
  }

  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency,
    maximumFractionDigits: 2,
  }).format(number);
}

function pct(number) {
  if (
    number === null ||
    number === undefined ||
    Number.isNaN(Number(number))
  ) {
    return "--";
  }

  return `${Number(number || 0).toFixed(2)}%`;
}

function getInitialPage() {
  const hash = window.location.hash.replace("#/", "") || "overview";

  return ALL_NAV.some((item) => item.id === hash)
    ? hash
    : "overview";
}

function App() {
  const [page, setPage] = useState(getInitialPage());
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [apiOk, setApiOk] = useState(false);

  const [token, setToken] = useState(
    localStorage.getItem("qmi_token") || ""
  );

  const [authError, setAuthError] = useState("");
  const [user, setUser] = useState(null);
  const [market, setMarket] = useState(null);
  const [portfolio, setPortfolio] = useState(null);
  const [ai, setAi] = useState(null);

  const [form, setForm] = useState({
    ticker: "",
    company: "",
    sector: "",
    quantity: "",
    average_price: "",
    current_price: "",
    notes: "",
  });

  const [editingId, setEditingId] = useState(null);

  const active =
    ALL_NAV.find((item) => item.id === page) || ALL_NAV[0];

  function navigate(nextPage) {
    setPage(nextPage);
    window.location.hash = `/${nextPage}`;
    setSidebarOpen(false);
  }

  async function load(activeToken = token) {
    try {
      await getHealth();
      setApiOk(true);

      if (!activeToken) {
        return;
      }

      const [
        userResult,
        marketResult,
        portfolioResult,
        aiResult,
      ] = await Promise.allSettled([
        getUser(activeToken),
        getMarket(activeToken),
        getPortfolio(activeToken),
        getAIStatus(activeToken),
      ]);

      const authenticationFailure = [
        userResult,
        marketResult,
        portfolioResult,
        aiResult,
      ].find(
        (result) =>
          result.status === "rejected" &&
          result.reason?.status === 401
      );

      if (authenticationFailure) {
        logout(false);
        return;
      }

      if (userResult.status === "fulfilled") {
        setUser(userResult.value);
      } else {
        console.error(
          "Unable to load user:",
          userResult.reason
        );
      }

      if (marketResult.status === "fulfilled") {
        setMarket(marketResult.value);
      } else {
        setMarket(null);
        console.error(
          "Unable to load market:",
          marketResult.reason
        );
      }

      if (portfolioResult.status === "fulfilled") {
        setPortfolio(portfolioResult.value);
      } else {
        setPortfolio(null);
        console.error(
          "Unable to load portfolio:",
          portfolioResult.reason
        );
      }

      if (aiResult.status === "fulfilled") {
        setAi(aiResult.value);
      } else {
        setAi(null);
        console.warn(
          "AI status endpoint unavailable:",
          aiResult.reason
        );
      }
    } catch (error) {
      console.error("Unable to connect to backend:", error);
      setApiOk(false);
    }
  }

  useEffect(() => {
    load(token);

    const onHashChange = () => {
      setPage(getInitialPage());
    };

    window.addEventListener("hashchange", onHashChange);

    return () => {
      window.removeEventListener(
        "hashchange",
        onHashChange
      );
    };
  }, [token]);

  const allocation = useMemo(
    () =>
      (portfolio?.positions || []).map((position) => ({
        ticker: position.ticker,
        value: position.value,
        weight: position.weight,
      })),
    [portfolio]
  );

  const sectorAllocation = useMemo(
    () => portfolio?.sector_allocation || [],
    [portfolio]
  );

  const trend = [
    { month: "Jan", value: 42 },
    { month: "Feb", value: 47 },
    { month: "Mar", value: 46 },
    { month: "Apr", value: 55 },
    { month: "May", value: 63 },
    { month: "Jun", value: 72 },
  ];

  async function savePosition(event) {
    event.preventDefault();

    const payload = {
      ticker: form.ticker,
      company: form.company || form.ticker,
      sector: form.sector || "Unclassified",
      quantity: Number(form.quantity),
      average_price: Number(form.average_price),
      current_price: Number(
        form.current_price || form.average_price
      ),
      currency: "USD",
      notes: form.notes || "",
    };

    const data = editingId
      ? await updatePosition(
          token,
          editingId,
          payload
        )
      : await createPosition(token, payload);

    if (data.portfolio) {
      setPortfolio(data.portfolio);
    }

    setEditingId(null);

    setForm({
      ticker: "",
      company: "",
      sector: "",
      quantity: "",
      average_price: "",
      current_price: "",
      notes: "",
    });
  }

  function startEdit(position) {
    setEditingId(position.id);

    setForm({
      ticker: position.ticker,
      company: position.company,
      sector: position.sector || "",
      quantity: String(position.quantity),
      average_price: String(position.average_price),
      current_price: String(position.current_price),
      notes: position.notes || "",
    });

    navigate("portfolio");
  }

  async function deletePosition(id) {
    const data = await deletePositionService(token, id);

    if (data.portfolio) {
      setPortfolio(data.portfolio);
    } else {
      load();
    }
  }

  async function login(email, password) {
    setAuthError("");

    try {
      const data = await loginService(email, password);

      localStorage.setItem(
        "qmi_token",
        data.access_token
      );

      setToken(data.access_token);
      setUser(data.user);
    } catch (error) {
      if (error.status === 401) {
        setAuthError("Invalid email or password");
        return;
      }

      setAuthError(
        "Backend authentication service unavailable"
      );
    }
  }

  async function logout(callApi = true) {
    if (callApi && token) {
      await logoutService(token).catch(() => null);
    }

    localStorage.removeItem("qmi_token");

    setToken("");
    setUser(null);
    setMarket(null);
    setPortfolio(null);
    setAi(null);
  }

  if (!token) {
    return (
      <LoginScreen
        apiOk={apiOk}
        authError={authError}
        login={login}
      />
    );
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
          {page === "overview" && (
            <Dashboard
              portfolio={portfolio}
              market={market}
              ai={ai}
            />
          )}

          {page === "market" && (
            <Market market={market} />
          )}

          {page === "portfolio" && (
            <Portfolio
              portfolio={portfolio}
              form={form}
              setForm={setForm}
              savePosition={savePosition}
              deletePosition={deletePosition}
              editingId={editingId}
              setEditingId={setEditingId}
              startEdit={startEdit}
            />
          )}

          {page === "ai" && <AI ai={ai} />}

          {page === "data" && (
            <DataPage
              portfolio={portfolio}
              market={market}
            />
          )}

          {page === "risk" && (
            <RiskPage portfolio={portfolio} />
          )}

          {page === "settings" && (
            <SettingsPage
              apiOk={apiOk}
              user={user}
            />
          )}

          {page === "ai-advisor" && (
            <AIInvestmentAdvisor />
          )}
        </PageShell>
      </main>
    </div>
  );
}

function LoginScreen({
  apiOk,
  authError,
  login,
}) {
  const [email, setEmail] = useState(
    "rodripereza8@gmail.com"
  );

  const [password, setPassword] =
    useState("qmi123");

  return (
    <div className="login-screen">
      <div className="login-card">
        <div className="logo">QMI</div>

        <div className="eyebrow">
          QUANTUM MARKET INTELLIGENCE · FOUNDATION
          v1.3
        </div>

        <h1>Secure Workspace Access</h1>

        <p>
          Authentication layer active. Sign in to
          access the institutional dashboard.
        </p>

        <form
          onSubmit={(event) => {
            event.preventDefault();
            login(email, password);
          }}
          className="login-form"
        >
          <label>Email</label>

          <input
            value={email}
            onChange={(event) =>
              setEmail(event.target.value)
            }
          />

          <label>Password</label>

          <input
            type="password"
            value={password}
            onChange={(event) =>
              setPassword(event.target.value)
            }
          />

          {authError && (
            <div className="auth-error">
              {authError}
            </div>
          )}

          <button type="submit">
            Enter QMI
          </button>
        </form>

        <div className="login-footer">
          <span className={apiOk ? "ok" : "bad"}>
            {apiOk ? "API OK" : "API OFFLINE"}
          </span>

          <span>
            Default user:
            rodripereza8@gmail.com / qmi123
          </span>
        </div>
      </div>
    </div>
  );
}

export default App;