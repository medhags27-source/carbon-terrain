import { useState } from "react";

import {

  Leaf,

  Bot,

  Users,

  IndianRupee,

  CalendarDays,

  MapPin,

  Clock,

  Sparkles,

  Send,

  Utensils,

  Zap,

  Trash2,

  Package,

} from "lucide-react";

import {

  PieChart,

  Pie,

  Cell,

  ResponsiveContainer,

  Tooltip,

} from "recharts";

import "./App.css";



const API = "http://127.0.0.1:8000";



function App() {

  const [eventCreated, setEventCreated] = useState(false);

  const [showWelcome, setShowWelcome] = useState(true);

  const [showLogin, setShowLogin] = useState(false);
  const [authMode, setAuthMode] = useState("login");
  const [authEmail, setAuthEmail] = useState("");
  const [authPassword, setAuthPassword] = useState("");
  const [authError, setAuthError] = useState("");
  const [authMessage, setAuthMessage] = useState("");
  const [authLoading, setAuthLoading] = useState(false);


  const [creating, setCreating] = useState(false);

  const [error, setError] = useState("");



  const [event, setEvent] = useState({

    event_name: "",

    event_type: "College Event",

    event_date: "",

    days: 1,

    attendees: "",

    budget: "",

    venue: "",

    distance_km: 10,

    meals_per_person_per_day: 1,

    energy_kwh: "",

    waste_kg: "",

    materials_kg: "",

  });



  const [dashboard, setDashboard] = useState(null);



  const [message, setMessage] = useState("");

  const [chat, setChat] = useState([]);

  const [loading, setLoading] = useState(false);

  const [carbonBudget, setCarbonBudget] = useState(0);

  const runCarbonBudget = async () => {

  try {

    setLoading(true);



    const response = await fetch(

      `${API}/optimize/carbon-budget?carbon_limit_kg=${carbonBudget || Number((total * 0.90).toFixed(2))}`,

      { method: "POST" }

    );



    const data = await response.json();



    if (!response.ok) {

      throw new Error(data.detail || "Carbon budget optimization failed");

    }



    setCarbonBudgetResult(data);

  } catch (error) {

    alert(error.message);

  } finally {

    setLoading(false);

  }

};



  const [optimizeResult, setOptimizeResult] = useState(null);

  const [carbonBudgetResult, setCarbonBudgetResult] = useState(null);



  const handleAuth = async (e) => {
    e.preventDefault();
    setAuthError("");
    setAuthMessage("");
    setAuthLoading(true);

    try {
      const endpoint = authMode === "register" ? "/auth/register" : "/auth/login";
      const response = await fetch(`${API}${endpoint}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email: authEmail.trim(), password: authPassword }),
      });
      const data = await response.json();

      if (!response.ok) {
        throw new Error(
          typeof data.detail === "string"
            ? data.detail
            : "Authentication failed. Please try again."
        );
      }

      if (authMode === "register") {
        setAuthMessage("Account created successfully. Please sign in.");
        setAuthMode("login");
        setAuthPassword("");
      } else {
        setShowLogin(false);
        setAuthPassword("");
        setAuthError("");
        setAuthMessage("");
      }
    } catch (err) {
      setAuthError(err.message || "Could not connect to the authentication server.");
    } finally {
      setAuthLoading(false);
    }
  };

  const today = new Date().toISOString().split("T")[0];



  const handleChange = (e) => {

    const { name, value } = e.target;



    setEvent((prev) => ({

      ...prev,

      [name]: value,

    }));

  };



  const createEvent = async (e) => {

    e.preventDefault();



    setError("");



    if (!event.event_name.trim()) {

      setError("Please enter an event name.");

      return;

    }



    if (!event.event_date) {

      setError("Please select the event date.");

      return;

    }



    if (event.event_date < today) {

      setError("Event date cannot be in the past.");

      return;

    }



    if (!event.attendees || Number(event.attendees) < 1) {

      setError("Please enter the expected number of attendees.");

      return;

    }



    if (event.budget === "" || Number(event.budget) < 0) {

      setError("Please enter a valid budget.");

      return;

    }



    setCreating(true);



    try {

      const payload = {

        event_name: event.event_name,

        event_type: event.event_type,

        event_date: event.event_date,

        days: Number(event.days),

        attendees: Number(event.attendees),

        budget: Number(event.budget),

        venue: event.venue,



        distance_km: Number(event.distance_km || 10),

        meals_per_person_per_day: Number(

          event.meals_per_person_per_day || 1

        ),



        energy_kwh:

          event.energy_kwh === ""

            ? null

            : Number(event.energy_kwh),



        waste_kg:

          event.waste_kg === ""

            ? null

            : Number(event.waste_kg),



        materials_kg:

          event.materials_kg === ""

            ? null

            : Number(event.materials_kg),

      };



      const response = await fetch(`${API}/event/setup`, {

        method: "POST",

        headers: {

          "Content-Type": "application/json",

        },

        body: JSON.stringify(payload),

      });



      const data = await response.json();



      if (!response.ok || !data.success) {

        throw new Error(

          data.message || "Could not create the event."

        );

      }



      setDashboard(data);

      setEventCreated(true);



      setChat([

        {

          type: "ai",

          text:

            `Your ${data.event.event_name} plan is ready. ` +

            `I calculated a baseline footprint of ` +

            `${data.carbon.total_co2e.toLocaleString()} kg CO₂e. ` +

            `Ask me what you should change, test another scenario, ` +

            `or optimize your budget.`,

        },

      ]);

    } catch (err) {

      setError(

        err.message ||

          "Could not connect to the planning engine."

      );

    } finally {

      setCreating(false);

    }

  };



  const sendMessage = async () => {

    if (!message.trim() || loading) return;



    const userMessage = message.trim();



    setMessage("");



    setChat((prev) => [

      ...prev,

      {

        type: "user",

        text: userMessage,

      },

    ]);



    setLoading(true);



    try {

      const response = await fetch(`${API}/assistant`, {

        method: "POST",

        headers: {

          "Content-Type": "application/json",

        },

        body: JSON.stringify({

          message: userMessage,

        }),

      });



      const data = await response.json();



      setChat((prev) => [

        ...prev,

        {

          type: "ai",

          text:

            data.message ||

            "I processed your request.",

          comparison: data.comparison || null,

        },

      ]);

    } catch {

      setChat((prev) => [

        ...prev,

        {

          type: "ai",

          text:

            "I couldn't connect to the planning engine. " +

            "Please make sure the backend is running.",

        },

      ]);

    } finally {

      setLoading(false);

    }

  };



  const handleKeyDown = (e) => {

    if (e.key === "Enter") {

      sendMessage();

    }

  };



  if (showWelcome) {

    return (

      <main className="welcome-page">

        <div className="welcome-card">

          <header className="welcome-nav">

            <div className="welcome-brand">

              <div className="welcome-logo">

                <Leaf size={25} />

              </div>

              <div>

                <div className="welcome-brand-name">EcoPlan AI</div>

                <div className="welcome-brand-subtitle">Sustainable Events</div>

              </div>

            </div>

            <span className="welcome-nav-label">AI-POWERED EVENT PLANNING</span>

          </header>



          <section className="welcome-hero">

            <div className="welcome-copy">

              <div className="welcome-eyebrow">

                <span className="welcome-status-dot"></span>

                PLAN WITH PURPOSE · CREATE WITH CARE

              </div>



              <h1>

                Smarter Planning.

                <span>A Lighter Footprint.</span>

              </h1>



              <p className="welcome-description">

                Bring your event to life while making thoughtful choices

                for the planet. Let AI help you plan an event that's

                kinder to the environment and mindful of your budget.

              </p>



              <button

                type="button"

                className="welcome-cta"

                onClick={() => { setShowWelcome(false); setShowLogin(true); }}

              >

                Get started with your event

                <span aria-hidden="true">→</span>

              </button>



              <p className="welcome-note">

                No carbon calculations needed to get started.

              </p>



              <div className="welcome-benefits">

                <div>

                  <span className="welcome-benefit-icon">

                    <Leaf size={17} />

                  </span>

                  <span>Carbon-aware planning</span>

                </div>

                <div>

                  <span className="welcome-benefit-icon">

                    <Sparkles size={17} />

                  </span>

                  <span>Personalized AI suggestions</span>

                </div>

                <div>

                  <span className="welcome-benefit-icon">

                    <IndianRupee size={17} />

                  </span>

                  <span>Budget-conscious decisions</span>

                </div>

              </div>

            </div>



            <div className="welcome-art" aria-label="Botanical EcoPlan illustration">

              <div className="welcome-art-ring welcome-art-ring-outer"></div>

              <div className="welcome-art-ring welcome-art-ring-inner"></div>

              <div className="welcome-art-leaf welcome-art-leaf-one">

                <Leaf size={56} strokeWidth={1.15} />

              </div>

              <div className="welcome-art-leaf welcome-art-leaf-two">

                <Leaf size={43} strokeWidth={1.15} />

              </div>

              <div className="welcome-art-leaf welcome-art-leaf-three">

                <Leaf size={32} strokeWidth={1.15} />

              </div>

              <div className="welcome-art-center">

                <Leaf size={29} strokeWidth={1.4} />

                <span>eco</span>

                <strong>by design</strong>

              </div>

              <span className="welcome-art-caption">

                A BETTER KIND OF EVENT

              </span>

            </div>

          </section>



          <footer className="welcome-footer">

            <span>Thoughtful events. Lighter impact.</span>

            <span>MADE FOR A GREENER TOMORROW</span>

          </footer>

        </div>

      </main>

    );

  }



if (showLogin) {
    return (
      <main className="login-page">
        <section className="login-card">
          <div className="login-brand">
            <div className="login-logo"><Leaf size={25} /></div>
            <div>
              <div className="login-brand-name">EcoPlan AI</div>
              <div className="login-brand-subtitle">Sustainable Events</div>
            </div>
          </div>

          <div className="login-heading">
            <span className="login-eyebrow">A GREENER WAY TO PLAN</span>
            <h1>
              {authMode === "login" ? <>Welcome <span>back.</span></> : <>Create your <span>account.</span></>}
            </h1>
            <p>
              {authMode === "login"
                ? "Sign in to continue planning thoughtful, sustainable events."
                : "Create an account to start planning greener events."}
            </p>
          </div>

          <form className="login-form" onSubmit={handleAuth}>
            <label>
              Email address
              <input type="email" placeholder="you@example.com" value={authEmail}
                onChange={(e) => setAuthEmail(e.target.value)} autoComplete="email" required />
            </label>

            <label>
              Password
              <input type="password"
                placeholder={authMode === "register" ? "Create a strong password" : "Enter your password"}
                value={authPassword} onChange={(e) => setAuthPassword(e.target.value)}
                autoComplete={authMode === "register" ? "new-password" : "current-password"}
                minLength={authMode === "register" ? 12 : 1} required />
            </label>

            {authMode === "register" && (
              <p className="login-demo-note">
                At least 6 characters, including uppercase and lowercase letters,
                a number, and a special character.
              </p>
            )}
            {authError && <div className="form-error" role="alert">{authError}</div>}
            {authMessage && <p className="login-success-message" role="status">{authMessage}</p>}

            <button className="login-submit" type="submit" disabled={authLoading}>
              {authLoading ? "Please wait..." : authMode === "login" ? "Sign in" : "Create account"}
              {!authLoading && <span> →</span>}
            </button>
          </form>

          <p className="login-switch">
            {authMode === "login" ? "New to EcoPlan AI? " : "Already have an account? "}
            <button type="button" onClick={() => {
              setAuthMode(authMode === "login" ? "register" : "login");
              setAuthError("");
              setAuthMessage("");
              setAuthPassword("");
            }}>
              {authMode === "login" ? "Create account" : "Sign in"}
            </button>
          </p>

          <button className="login-back" type="button" onClick={() => {
            setShowLogin(false);
            setShowWelcome(true);
            setAuthError("");
            setAuthMessage("");
          }}>← Back to welcome</button>
        </section>
      </main>
    );
  }

  if (!eventCreated) {

    return (

      <div className="setup-page">

        <div className="setup-card">

          <div className="setup-brand">

            <div className="brand-icon">

              <Leaf size={24} />

            </div>



            <div>

              <div className="brand-title">

                EcoPlan AI

              </div>

              <div className="brand-subtitle">

                Sustainable Events

              </div>

            </div>

          </div>



          <div className="setup-header">

  <div className="setup-kicker">

    <span className="hero-kicker-dot"></span>

    AI EVENT PLANNING ASSISTANT

  </div>



  <div className="hero-layout">

    <div className="hero-copy">

      <div className="hero-eyebrow">PLAN WITH PURPOSE</div>

      <h1>Smarter Planning.<br /><span>A Lighter Footprint.</span></h1>

      <p>

        Bring your event to life while making thoughtful choices

        for the planet. Tell us your plans and let EcoPlan AI

        help you find a more sustainable way forward.

      </p>

      <div className="hero-points">

        <span>♧ Carbon-aware planning</span>

        <span>✳ Practical AI suggestions</span>

      </div>

    </div>



    <div className="hero-botanical" aria-hidden="true">

      <div className="botanical-orbit botanical-orbit-one"></div>

      <div className="botanical-orbit botanical-orbit-two"></div>

      <div className="botanical-leaf botanical-leaf-one">♧</div>

      <div className="botanical-leaf botanical-leaf-two">♧</div>

      <div className="botanical-leaf botanical-leaf-three">♧</div>

      <div className="botanical-center">

        <span>eco</span>

        <strong>by design</strong>

      </div>

      <span className="botanical-caption">A BETTER KIND OF EVENT</span>

    </div>

  </div>



  <div className="hero-divider">

    <span></span>

    <span>LET'S BUILD YOUR EVENT PLAN</span>

    <span></span>

  </div>

</div>

<form

            className="event-form"

            onSubmit={createEvent}

          >

            <div className="form-section">

              <h2>Event details</h2>



              <div className="form-grid">

                <label>

                  Event name *

                  <input

                    name="event_name"

                    value={event.event_name}

                    onChange={handleChange}

                    placeholder="e.g. AIML Tech Fest"

                  />

                </label>



                <label>

                  Event type *

                  <select

                    name="event_type"

                    value={event.event_type}

                    onChange={handleChange}

                  >

                    <option>College Event</option>

                    <option>Conference</option>

                    <option>Workshop</option>

                    <option>Fest</option>

                    <option>Exhibition</option>

                    <option>Corporate Event</option>

                    <option>Other</option>

                  </select>

                </label>



                <label>

                  Event date *

                  <input

                    type="date"

        onClick={(e) => e.currentTarget.showPicker?.()}

                    name="event_date"

                    min={today}

                    value={event.event_date}

                    onChange={handleChange}

                  />

                  <small>

                    Only today or future dates are allowed.

                  </small>

                </label>



                <label>

                  Duration (days) *

                  <input

                    type="number"

                    min="1"

                    name="days"

                    value={event.days}

                    onChange={handleChange}

                  />

                </label>



                <label>

                  Expected attendees *

                  <input

                    type="number"

                    min="1"

                    name="attendees"

                    value={event.attendees}

                    onChange={handleChange}

                    placeholder="e.g. 1000"

                  />

                </label>



                <label>

                  Budget (₹) *

                  <input

                    type="number"

                    min="0"

                    name="budget"

                    value={event.budget}

                    onChange={handleChange}

                    placeholder="e.g. 300000"

                  />

                </label>



                <label className="full">

                  Venue / location *

                  <input

                    name="venue"

                    value={event.venue}

                    onChange={handleChange}

                    placeholder="e.g. BMSITM, Bengaluru"

                  />

                </label>

              </div>

            </div>



            <div className="form-section">

              <h2>Planning inputs</h2>



              <p className="section-note">

                These help improve the carbon estimate.

                Optional values can be left blank.

              </p>



              <div className="form-grid">

                <label>

                  Average travel distance (km)

                  <input

                    type="number"

                    min="0"

                    name="distance_km"

                    value={event.distance_km}

                    onChange={handleChange}

                  />

                  <small>

                    Used as a planning estimate.

                  </small>

                </label>



                <label>

                  Meals per person / day

                  <input

                    type="number"

                    min="0"

                    step="0.5"

                    name="meals_per_person_per_day"

                    value={

                      event.meals_per_person_per_day

                    }

                    onChange={handleChange}

                  />

                </label>



                <label>

                  Energy usage (kWh)

                  <input

                    type="number"

                    min="0"

                    name="energy_kwh"

                    value={event.energy_kwh}

                    onChange={handleChange}

                    placeholder="Optional"

                  />

                </label>



                <label>

                  Waste (kg)

                  <input

                    type="number"

                    min="0"

                    name="waste_kg"

                    value={event.waste_kg}

                    onChange={handleChange}

                    placeholder="Optional"

                  />

                </label>



                <label>

                  Materials (kg)

                  <input

                    type="number"

                    min="0"

                    name="materials_kg"

                    value={event.materials_kg}

                    onChange={handleChange}

                    placeholder="Optional"

                  />

                </label>

              </div>

            </div>



            {error && (

              <div className="form-error">

                {error}

              </div>

            )}



            <div className="setup-footer">

              <div>

                <strong>Carbon limit?</strong>

                <span>

                  You don't need to know it.

                  EcoPlan AI will recommend a planning target

                  from your calculated baseline.

                </span>

              </div>



              <button

                className="create-button"

                type="submit"

                disabled={creating}

              >

                <Sparkles size={18} />

                {creating

                  ? "Generating plan..."

                  : "Generate Sustainable Plan"}

              </button>

            </div>

          </form>

        </div>

      </div>

    );

  }



  const carbon = dashboard.carbon;



  const carbonData = [

    {

      name: "Energy",

      value: carbon.energy,

    },

    {

      name: "Food",

      value: carbon.food,

    },

    {

      name: "Transport",

      value: carbon.transport,

    },

    {

      name: "Waste",

      value: carbon.waste,

    },

    {

      name: "Materials",

      value: carbon.materials,

    },

  ];



  const total = carbon.total_co2e;

  const target =

    dashboard.recommended_carbon_limit_kg;



  const sustainabilityScore = Math.max(

    0,

    Math.min(

      100,

      Math.round(100 - (total / Math.max(target, 1) - 1) * 50)

    )

  );



  return (

    <div className="app">

      <aside className="sidebar">

        <div className="brand">

          <div className="brand-icon">

            <Leaf size={21} />

          </div>



          <div>

            <div className="brand-title">

              EcoPlan AI

            </div>

            <div className="brand-subtitle">

              Sustainable Events

            </div>

          </div>

        </div>



        <nav>

          <button className="nav-item active">

            Overview

          </button>



          <button className="nav-item">

            <Sparkles size={18} />

            AI Planner

          </button>



          <button className="nav-item">

            <Zap size={18} />

            Impact Optimizer

          </button>

        </nav>



        <div className="sidebar-event">

          <div className="small-label">

            CURRENT EVENT

          </div>



          <strong>

            {dashboard.event.event_name}

          </strong>



          <span>

            {dashboard.event.days}-day event ·{" "}

            {dashboard.event.attendees.toLocaleString()} attendees

          </span>

        </div>



        <div className="sidebar-bottom">

          <div className="status-dot"></div>

          Planning engine online

        </div>

      </aside>



      <main className="main">

        <header className="topbar">

          <div>

            <div className="eyebrow">

              EVENT PLANNING ASSISTANT

            </div>



            <h1>

              {dashboard.event.event_name}

            </h1>



            <p>

              Optimize your event for impact, cost and carbon.

            </p>

          </div>



          <button

  className="optimize-button"

  onClick={async () => {

    try {

      setLoading(true);



      const response = await fetch(

        `${API}/optimize/impact?extra_budget=50000`,

        { method: "POST" }

      );



      const data = await response.json();



      if (!response.ok) {

        throw new Error(data.detail || "Optimization failed");

      }



      setOptimizeResult(data.recommendation);

    } catch (error) {

      console.error("Optimization error:", error);

      setError(error.message || "Could not optimize the event.");

    } finally {

      setLoading(false);

    }

  }}

  disabled={loading}

>

  <Sparkles size={17} />

  {loading ? "Optimizing..." : "Optimize Event"}

</button>

        </header>



        {optimizeResult && (

          <section className="decision-engine">

            <div className="decision-header">

              <div>

                <span className="section-label">DECISION ENGINE</span>

                <h2>Recommended sustainability actions</h2>

                <p>

                  The optimizer compares feasible interventions and selects

                  the combination with the highest estimated carbon impact

                  within the additional budget.

                </p>

              </div>

            </div>



            <div className="decision-summary">

              <div>

                <strong>

                  {Number(optimizeResult.total_co2_saved_kg || 0).toFixed(2)} kg

                </strong>

                <span>estimated CO₂e reduction</span>

              </div>



              <div>

                <strong>

                  ₹{Number(optimizeResult.total_cost_inr || 0).toLocaleString()}

                </strong>

                <span>additional cost</span>

              </div>



              <div>

                <strong>

                  ₹{Number(

                    optimizeResult.remaining_budget_inr || 0

                  ).toLocaleString()}

                </strong>

                <span>remaining budget</span>

              </div>

            </div>



            <div className="intervention-list">

              {optimizeResult.selected?.map((item) => (

                <div className="intervention-card" key={item.id}>

                  <div>

                    <strong>{item.name}</strong>

                    <p>{item.basis}</p>

                  </div>



                  <div className="intervention-impact">

                    <strong>

                      {Number(item.co2_saved_kg || 0).toFixed(2)} kg

                    </strong>

                    <span>CO₂e saved</span>

                  </div>



                  <div className="intervention-cost">

                    <strong>

                      ₹{Number(item.cost_inr || 0).toLocaleString()}

                    </strong>

                    <span>estimated cost</span>

                  </div>

                </div>

              ))}

            </div>

          </section>

        )}

        <section className="metrics">

          <div className="metric-card carbon">

            <div className="metric-top">

              <span>Carbon footprint</span>

              <div className="metric-icon">

                <Leaf size={17} />

              </div>

            </div>



            <div className="metric-value">

              {total.toLocaleString()}

            </div>



            <div className="metric-unit">

              kg CO₂e estimated

            </div>



            <div className="metric-note">

              Recommended target:{" "}

              {target.toLocaleString()} kg

            </div>

          </div>



          <div className="metric-card">

            <div className="metric-top">

              <span>Event budget</span>

              <div className="metric-icon">

                <IndianRupee size={17} />

              </div>

            </div>



            <div className="metric-value">

              ₹{(

                dashboard.event.budget / 100000

              ).toFixed(1)}L

            </div>



            <div className="metric-unit">

              planned budget

            </div>



            <div className="metric-note">

              {dashboard.event.venue}

            </div>

          </div>



          <div className="metric-card">

            <div className="metric-top">

              <span>Attendance</span>

              <div className="metric-icon">

                <Users size={17} />

              </div>

            </div>



            <div className="metric-value">

              {dashboard.event.attendees.toLocaleString()}

            </div>



            <div className="metric-unit">

              expected attendees

            </div>



            <div className="metric-note">

              {dashboard.event.days} event day

              {dashboard.event.days !== 1 ? "s" : ""}

            </div>

          </div>



          <div className="metric-card">

            <div className="metric-top">

              <span>Sustainability score</span>

              <div className="metric-icon">

                <Sparkles size={17} />

              </div>

            </div>



            <div className="metric-value">

              {sustainabilityScore}

              <span className="score-small">

                /100

              </span>

            </div>



            <div className="metric-unit">

              current planning score

            </div>



            <div className="metric-note">

              AI-generated baseline

            </div>

          </div>

        </section>



        <section className="grid-two">

          <div className="panel carbon-panel">

            <div className="panel-header">

              <div>

                <div className="panel-kicker">

                  EMISSIONS ANALYSIS

                </div>

                <h2>Carbon breakdown</h2>

              </div>

            </div>



            <div className="chart-area">

              <div className="donut">

                <ResponsiveContainer

                  width="100%"

                  height="100%"

                >

                  <PieChart>

                    <Pie

                      data={carbonData}

                      dataKey="value"

                      nameKey="name"

                      innerRadius={65}

                      outerRadius={92}

                      paddingAngle={3}

                    >

                      {carbonData.map((_, index) => (

                        <Cell key={index} />

                      ))}

                    </Pie>



                    <Tooltip />

                  </PieChart>

                </ResponsiveContainer>



                <div className="donut-center">

                  <strong>

                    {(total / 1000).toFixed(2)}T

                  </strong>

                  <span>CO₂e</span>

                </div>

              </div>



              <div className="legend">

                {carbonData.map((item, index) => (

                  <div

                    className="legend-row"

                    key={item.name}

                  >

                    <div className="legend-name">

                      <span

                        className={`legend-dot dot-${index}`}

                      ></span>



                      {item.name}

                    </div>



                    <strong>

                      {item.value.toLocaleString()} kg

                    </strong>

                  </div>

                ))}

              </div>

            </div>

          </div>



          <div className="panel assistant-panel">

            <div className="panel-header">

              <div>

                <div className="panel-kicker">

                  AI ASSISTANT

                </div>

                <h2>Ask your planner</h2>

              </div>



              <div className="online">

                ● Online

              </div>

            </div>



            <div className="chat">

              {chat.map((item, index) => (

                <div

                  key={index}

                  className={`chat-message ${item.type}`}

                >

                  {item.type === "ai" && (

                    <div className="bot-avatar">

                      <Bot size={15} />

                    </div>

                  )}



                  <div className="chat-bubble">

                    {item.text}

                  </div>





                  {item.comparison && (

                    <div className="decision-card">

                      {item.comparison.mode === "what_if" ? (

                        <>

                          <div className="decision-card-top">

                            <div>

                              <span className="decision-kicker">

                                SCENARIO LAB

                              </span>

                              <h3>What-If Scenario</h3>

                            </div>

                            <span className="scenario-badge">SIMULATION</span>

                          </div>



                          <p className="decision-question">

                            What happens if the event has{" "}

                            <strong>

                              {item.comparison.after.attendees?.toLocaleString()}

                            </strong>{" "}

                            attendees?

                          </p>



                          <div className="scenario-columns">

                            <div className="scenario-column current">

                              <span className="scenario-label">

                                CURRENT EVENT

                              </span>

                              <strong>

                                {item.comparison.before.attendees?.toLocaleString()}

                              </strong>

                              <small>attendees</small>



                              <div className="scenario-stat">

                                <span>Carbon</span>

                                <strong>

                                  {Number(

                                    item.comparison.before.co2_kg || 0

                                  ).toFixed(2)}{" "}

                                  kg

                                </strong>

                              </div>



                              <div className="scenario-stat">

                                <span>Transport cost</span>

                                <strong>

                                  ₹{Number(

                                    item.comparison.before.cost || 0

                                  ).toLocaleString()}

                                </strong>

                              </div>

                            </div>



                            <div className="scenario-arrow">→</div>



                            <div className="scenario-column projected">

                              <span className="scenario-label">

                                SCENARIO

                              </span>

                              <strong>

                                {item.comparison.after.attendees?.toLocaleString()}

                              </strong>

                              <small>attendees</small>



                              <div className="scenario-stat">

                                <span>Carbon</span>

                                <strong>

                                  {Number(

                                    item.comparison.after.co2_kg || 0

                                  ).toFixed(2)}{" "}

                                  kg

                                </strong>

                              </div>



                              <div className="scenario-stat">

                                <span>Transport cost</span>

                                <strong>

                                  ₹{Number(

                                    item.comparison.after.cost || 0

                                  ).toLocaleString()}

                                </strong>

                              </div>

                            </div>

                          </div>



                          <div className="scenario-impact">

                            <div>

                              <span>Carbon impact</span>

                              <strong>

                                {item.comparison.change.co2_kg >= 0

                                  ? "+"

                                  : ""}

                                {Number(

                                  item.comparison.change.co2_kg || 0

                                ).toFixed(2)}{" "}

                                kg CO₂e

                              </strong>

                            </div>



                            <div>

                              <span>Cost impact</span>

                              <strong>

                                {item.comparison.change.cost >= 0

                                  ? "+"

                                  : "-"}

                                ₹{Number(

                                  Math.abs(

                                    item.comparison.change.cost || 0

                                  )

                                ).toLocaleString()}

                              </strong>

                            </div>

                          </div>



                          <div className="scenario-note">

                            This is a simulation. Your actual event has not

                            been changed.

                          </div>

                        </>

                      ) : (

                        <>

                          <div className="decision-card-top">

                            <div>

                              <span className="decision-kicker">

                                DECISION IMPACT

                              </span>

                              <h3>Event Re-optimized</h3>

                            </div>

                            <span className="update-badge">UPDATED</span>

                          </div>



                          <p className="decision-question">

                            Your event changed from{" "}

                            <strong>

                              {item.comparison.before.attendees?.toLocaleString()}

                            </strong>{" "}

                            to{" "}

                            <strong>

                              {item.comparison.after.attendees?.toLocaleString()}

                            </strong>{" "}

                            attendees.

                          </p>



                          <div className="scenario-columns">

                            <div className="scenario-column current">

                              <span className="scenario-label">BEFORE</span>

                              <strong>

                                {Number(

                                  item.comparison.before.co2_kg || 0

                                ).toFixed(2)}

                              </strong>

                              <small>kg CO₂e</small>



                              <div className="scenario-stat">

                                <span>Transport cost</span>

                                <strong>

                                  ₹{Number(

                                    item.comparison.before.cost || 0

                                  ).toLocaleString()}

                                </strong>

                              </div>

                            </div>



                            <div className="scenario-arrow">→</div>



                            <div className="scenario-column projected">

                              <span className="scenario-label">AFTER</span>

                              <strong>

                                {Number(

                                  item.comparison.after.co2_kg || 0

                                ).toFixed(2)}

                              </strong>

                              <small>kg CO₂e</small>



                              <div className="scenario-stat">

                                <span>Transport cost</span>

                                <strong>

                                  ₹{Number(

                                    item.comparison.after.cost || 0

                                  ).toLocaleString()}

                                </strong>

                              </div>

                            </div>

                          </div>



                          <div className="scenario-impact">

                            <div>

                              <span>Carbon change</span>

                              <strong>

                                {item.comparison.change.co2_kg >= 0

                                  ? "+"

                                  : ""}

                                {Number(

                                  item.comparison.change.co2_kg || 0

                                ).toFixed(2)}{" "}

                                kg CO₂e

                              </strong>

                            </div>



                            <div>

                              <span>Cost change</span>

                              <strong>

                                {item.comparison.change.cost >= 0

                                  ? "+"

                                  : "-"}

                                ₹{Number(

                                  Math.abs(

                                    item.comparison.change.cost || 0

                                  )

                                ).toLocaleString()}

                              </strong>

                            </div>

                          </div>



                          {item.comparison.explanation && (

                            <div className="scenario-note">

                              <strong>Why:</strong>{" "}

                              {item.comparison.explanation}

                            </div>

                          )}

                        </>

                      )}

                    </div>

                  )}

                </div>

              ))}



              {loading && (

                <div className="chat-message ai">

                  <div className="bot-avatar">

                    <Bot size={15} />

                  </div>



                  <div className="chat-bubble typing">

                    Thinking...

                  </div>

                </div>

              )}

            </div>



            <div className="quick-actions">

              <button

                onClick={() =>

                  setMessage(

                    "I have 50000 extra budget. What should I spend it on?"

                  )

                }

              >

                ₹50k extra budget

              </button>



              <button

                onClick={() =>

                  setMessage(

                    "What if 1500 students attend?"

                  )

                }

              >

                What if 1500 attend?

              </button>

            </div>



            <div className="chat-input">

              <input

                value={message}

                onChange={(e) =>

                  setMessage(e.target.value)

                }

                onKeyDown={handleKeyDown}

                placeholder="Ask about your event..."

              />



              <button onClick={sendMessage}>

                <Send size={17} />

              </button>

            </div>

          </div>

        </section>

      <section className="panel">

        <div className="section-heading">

          <div>

            <span className="eyebrow">CARBON GOAL</span>

            <h2>How green do you want your event to be?</h2>

            <p>

              We calculate the target from your event baseline. You don't

              need to know a carbon limit yourself.

            </p>

          </div>

        </div>



        <div className="budget-grid">

          <div>

            <span>Calculated baseline</span>

            <strong>{total.toFixed(2)} kg CO₂e</strong>

          </div>



          <div>

            <span>Balanced target</span>

            <strong>{(total * 0.90).toFixed(2)} kg CO₂e</strong>

          </div>

        </div>



        <div className="goal-options">

          <button

            className={carbonBudget === total * 0.90 ? "goal-option active" : "goal-option"}

            onClick={() => setCarbonBudget(Number((total * 0.90).toFixed(2)))}

          >

            <strong>🌱 Balanced</strong>

            <span>10% lower carbon</span>

          </button>



          <button

            className={carbonBudget === total * 0.80 ? "goal-option active" : "goal-option"}

            onClick={() => setCarbonBudget(Number((total * 0.80).toFixed(2)))}

          >

            <strong>🌿 Greener</strong>

            <span>20% lower carbon</span>

          </button>



          <button

            className={carbonBudget === total * 0.70 ? "goal-option active" : "goal-option"}

            onClick={() => setCarbonBudget(Number((total * 0.70).toFixed(2)))}

          >

            <strong>🌎 Aggressive</strong>

            <span>30% lower carbon</span>

          </button>

        </div>



        <div className="budget-row">

          <div>

            <label>Selected carbon target</label>

            <strong>{(carbonBudget || Number((total * 0.90).toFixed(2))).toFixed(2)} kg CO₂e</strong>

          </div>



          <button

            className="optimize-button"

            onClick={runCarbonBudget}

            disabled={loading}

          >

            <Sparkles size={17} />

            {loading ? "Checking..." : "Check Feasibility"}

          </button>

        </div>



        {carbonBudgetResult && (

          <div className="budget-result">

            <div className="result-status">

              <strong>

                {carbonBudgetResult.status === "already_feasible"

                  ? "✓ Your target is achievable"

                  : carbonBudgetResult.status === "infeasible"

                  ? "⚠ Your target needs stronger measures"

                  : "✓ Optimized plan found"}

              </strong>

            </div>



            <div className="budget-grid">

              <div>

                <span>Current footprint</span>

                <strong>

                  {carbonBudgetResult.current_footprint_kg} kg

                </strong>

              </div>



              <div>

                <span>Target</span>

                <strong>

                  {carbonBudgetResult.carbon_limit_kg} kg

                </strong>

              </div>



              <div>

                <span>Best achievable</span>

                <strong>

                  {carbonBudgetResult.optimized_footprint_kg} kg

                </strong>

              </div>



              <div>

                <span>Additional cost</span>

                <strong>

                  ₹{carbonBudgetResult.additional_cost_inr}

                </strong>

              </div>

            </div>



            <p className="budget-message">

              {carbonBudgetResult.message}

            </p>



            {carbonBudgetResult.status === "infeasible" && (

              <div className="warning-box">

                Remaining gap:{" "}

                <strong>

                  {carbonBudgetResult.remaining_excess_co2_kg} kg CO₂e

                </strong>

              </div>

            )}



            {carbonBudgetResult.selected_interventions?.length > 0 && (

              <div className="intervention-list">

                <h3>Recommended changes</h3>



                {carbonBudgetResult.selected_interventions.map(

                  (item, index) => (

                    <div className="intervention-item" key={index}>

                      <strong>{item.name}</strong>

                      <span>

                        Save {item.co2_saved_kg} kg CO₂e · ₹{item.cost_inr}

                      </span>

                    </div>

                  )

                )}

              </div>

            )}

          </div>

        )}

      </section>



      </main>

    </div>

  );

}



export default App;


























