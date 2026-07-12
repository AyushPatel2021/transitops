<template>
  <main class="landing-page">
    <section class="hero-section">
      <nav class="landing-nav" aria-label="Main navigation">
        <button class="brand" type="button" @click="$router.push('/')">
          <img :src="logoIcon" alt="" />
          <span>TransitOps</span>
        </button>
        <div class="nav-actions">
          <button type="button" class="nav-link" @click="$router.push('/login')">Sign in</button>
          <button type="button" class="nav-button" @click="$router.push('/signup')">Create account</button>
        </div>
      </nav>

      <div class="hero-grid">
        <div class="hero-copy">
          <p class="eyebrow">Fleet operations workspace</p>
          <h1>Dispatch trips, watch vehicles, and track cost without switching systems.</h1>
          <p class="lede">
            TransitOps gives transport teams one working view for vehicles, regions, drivers, trips, maintenance,
            fuel, expenses, users, and reports. Every screen follows the same role-aware operating model.
          </p>
          <div class="hero-actions">
            <button type="button" class="primary-button" @click="$router.push('/login')">Open dashboard</button>
            <button type="button" class="secondary-button" @click="$router.push('/signup')">Add operational user</button>
          </div>
          <div class="trust-row" aria-label="Implemented module status">
            <span>Auth and roles</span>
            <span>Trip engine</span>
            <span>Maintenance and finance</span>
            <span>Reports</span>
          </div>
        </div>

        <div class="product-frame" aria-label="TransitOps dashboard preview">
          <div class="frame-topbar">
            <div class="window-controls"><span></span><span></span><span></span></div>
            <strong>Fleet command</strong>
            <em>All time</em>
          </div>
          <div class="frame-body">
            <aside class="mock-sidebar">
              <img :src="logoIcon" alt="" />
              <span class="active">Dashboard</span>
              <span>Vehicles</span>
              <span>Trip Board</span>
              <span>Maintenance</span>
              <span>Reports</span>
            </aside>
            <div class="mock-main">
              <div class="mock-kpis">
                <div><strong>8</strong><span>Active vehicles</span></div>
                <div><strong>2</strong><span>Active trips</span></div>
                <div><strong>1</strong><span>In shop</span></div>
                <div><strong>25%</strong><span>Utilization</span></div>
              </div>
              <div class="mock-content">
                <section class="mock-card chart-card">
                  <div class="card-heading">
                    <strong>Trip volume</strong>
                    <span>Jul 01 - Jul 12</span>
                  </div>
                  <div class="bar-chart" aria-hidden="true">
                    <span style="height: 18%"></span>
                    <span style="height: 32%"></span>
                    <span style="height: 26%"></span>
                    <span style="height: 55%"></span>
                    <span style="height: 42%"></span>
                    <span style="height: 90%"></span>
                  </div>
                </section>
                <section class="mock-card board-card">
                  <div class="card-heading">
                    <strong>Dispatch board</strong>
                    <span>Live</span>
                  </div>
                  <div class="board-row"><b>TRK-003</b><span>South Zone</span><em>On trip</em></div>
                  <div class="board-row"><b>VAN-005</b><span>Central Zone</span><em class="warn">In shop</em></div>
                  <div class="board-row"><b>VAN-007</b><span>North Zone</span><em>Available</em></div>
                </section>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>

    <section class="module-section">
      <div class="section-title">
        <p class="eyebrow">Daily operations</p>
        <h2>The core screens a transport team opens every day.</h2>
      </div>
      <div class="module-grid">
        <article v-for="item in modules" :key="item.title" class="module-card">
          <component :is="item.icon" class="module-icon" />
          <h3>{{ item.title }}</h3>
          <p>{{ item.copy }}</p>
        </article>
      </div>
    </section>

    <section class="workflow-section">
      <div class="section-title">
        <p class="eyebrow">Trip lifecycle</p>
        <h2>Rules are enforced where they matter: on the server.</h2>
      </div>
      <div class="workflow-board">
        <article>
          <span>Draft</span>
          <p>Choose available vehicles and eligible drivers. Cargo must fit the vehicle capacity.</p>
        </article>
        <article>
          <span>Dispatched</span>
          <p>Vehicle and driver are locked to the trip, preventing double-booking.</p>
        </article>
        <article>
          <span>Completed</span>
          <p>Final odometer, fuel liters, and fuel cost create the linked fuel log automatically.</p>
        </article>
        <article>
          <span>Cancelled</span>
          <p>Draft trips close cleanly. Dispatched trips restore vehicle and driver availability.</p>
        </article>
      </div>
    </section>

    <section class="split-section">
      <div class="copy-panel">
        <p class="eyebrow">Cost control</p>
        <h2>Maintenance, fuel, and expenses are connected to the fleet record.</h2>
        <p>
          Start a maintenance log and the vehicle leaves the dispatch pool. Close it with an end date and the vehicle
          returns unless it was retired. Fuel and maintenance totals roll into operational cost reporting.
        </p>
      </div>
      <div class="report-panel">
        <div class="report-row">
          <span>Fuel Efficiency</span>
          <strong>km/L</strong>
        </div>
        <div class="report-row">
          <span>Fleet Utilization</span>
          <strong>by region</strong>
        </div>
        <div class="report-row">
          <span>Operational Cost</span>
          <strong>fuel + maintenance</strong>
        </div>
        <div class="report-row">
          <span>ROI</span>
          <strong>cost vs revenue</strong>
        </div>
      </div>
    </section>

    <section class="role-section">
      <div class="section-title">
        <p class="eyebrow">Access model</p>
        <h2>Each role sees the work it is responsible for.</h2>
      </div>
      <div class="role-grid">
        <article v-for="role in roles" :key="role.name">
          <strong>{{ role.name }}</strong>
          <p>{{ role.copy }}</p>
        </article>
      </div>
    </section>

    <section class="cta-section">
      <div>
        <p class="eyebrow">Ready for the next run</p>
        <h2>Open TransitOps and manage the fleet from the same workspace.</h2>
      </div>
      <div class="hero-actions">
        <button type="button" class="primary-button" @click="$router.push('/login')">Sign in</button>
        <button type="button" class="secondary-button" @click="$router.push('/signup')">Create account</button>
      </div>
    </section>
  </main>
</template>

<script setup lang="ts">
import {
  Activity,
  BadgeDollarSign,
  ClipboardList,
  Fuel,
  Gauge,
  MapPinned,
  ShieldCheck,
  Truck,
  UserCheck,
  Wrench,
} from 'lucide-vue-next'
import logoIcon from '../assets/transitops_mark.svg'

const modules = [
  { title: 'Vehicles', icon: Truck, copy: 'Track registration, capacity, odometer, lifecycle status, and operating region.' },
  { title: 'Regions', icon: MapPinned, copy: 'Keep operating zones clean so fleet, driver, and report filters stay usable.' },
  { title: 'Drivers', icon: UserCheck, copy: 'Manage licenses, safety score, availability, and compliance status.' },
  { title: 'Trips', icon: ClipboardList, copy: 'Move trips from draft to dispatched, completed, or cancelled with backend validation.' },
  { title: 'Maintenance', icon: Wrench, copy: 'Move vehicles in and out of shop through maintenance records, not manual guesses.' },
  { title: 'Fuel and expenses', icon: Fuel, copy: 'Capture liters, fuel price, tolls, fines, and other operating costs.' },
  { title: 'Reports', icon: Gauge, copy: 'Review efficiency, utilization, operational cost, and ROI with CSV export.' },
  { title: 'Access control', icon: ShieldCheck, copy: 'Role-based menus and record permissions keep work scoped to each team.' },
]

const roles = [
  { name: 'Admin', copy: 'Owns setup, users, roles, unlocks, and full operational access.' },
  { name: 'Fleet Manager', copy: 'Runs vehicles, regions, maintenance, trips, and dispatch decisions.' },
  { name: 'Driver', copy: 'Works with trips they created or trips assigned to their driver record.' },
  { name: 'Safety Officer', copy: 'Maintains driver compliance, suspension, reinstatement, and safety data.' },
  { name: 'Financial Analyst', copy: 'Controls fuel logs, expenses, and cost-focused reporting.' },
]

void Activity
void BadgeDollarSign
</script>

<style lang="scss" scoped>
.landing-page {
  min-height: 100vh;
  background: #0b1016;
  color: #eef4fb;
}

button {
  font: inherit;
}

.hero-section {
  min-height: 100vh;
  padding: 1.25rem clamp(1rem, 4vw, 4rem) 1.5rem;
  background:
    linear-gradient(180deg, rgba(11, 16, 22, 0.18), #0b1016 82%),
    url('https://images.unsplash.com/photo-1500530855697-b586d89ba3ee?auto=format&fit=crop&w=1800&q=80') center / cover;
}

.landing-nav {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 1rem;
}

.brand {
  display: inline-flex;
  align-items: center;
  gap: 0.75rem;
  border: 0;
  background: transparent;
  color: #fff;
  cursor: pointer;
  font-size: 1.125rem;
  font-weight: 800;

  img {
    width: 2rem;
    height: 2rem;
  }
}

.nav-actions,
.hero-actions {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 0.75rem;
}

.nav-link {
  border: 0;
  background: transparent;
  color: #d4deea;
  cursor: pointer;
}

.nav-button,
.primary-button,
.secondary-button {
  border-radius: 8px;
  cursor: pointer;
  transition: background 0.16s ease, border-color 0.16s ease, transform 0.16s ease;
}

.nav-button {
  padding: 0.62rem 1rem;
  border: 1px solid rgba(255, 255, 255, 0.18);
  background: rgba(255, 255, 255, 0.1);
  color: #fff;
}

.primary-button,
.secondary-button {
  min-height: 2.75rem;
  padding: 0.72rem 1.1rem;
  border: 1px solid transparent;
  font-weight: 750;
}

.primary-button {
  background: #2f6fed;
  color: #fff;
}

.secondary-button {
  background: rgba(255, 255, 255, 0.1);
  border-color: rgba(255, 255, 255, 0.18);
  color: #eef4fb;
}

.nav-button:hover,
.primary-button:hover,
.secondary-button:hover {
  transform: translateY(-1px);
}

.hero-grid {
  display: grid;
  grid-template-columns: minmax(0, 0.95fr) minmax(520px, 1.05fr);
  align-items: center;
  gap: clamp(1.5rem, 3.5vw, 3.5rem);
  min-height: calc(100vh - 5.25rem);
  padding-top: 0.75rem;
}

.hero-copy {
  max-width: 760px;
}

.eyebrow {
  margin: 0 0 0.9rem;
  color: #8fd7ff;
  font-size: 0.76rem;
  font-weight: 850;
  letter-spacing: 0.12em;
  text-transform: uppercase;
}

h1,
h2,
h3,
p {
  margin-top: 0;
}

h1 {
  margin-bottom: 1rem;
  color: #fff;
  font-size: clamp(2.7rem, 5.1vw, 4.85rem);
  line-height: 0.98;
  letter-spacing: 0;
}

.lede {
  max-width: 650px;
  color: #d4deea;
  font-size: clamp(0.98rem, 1.25vw, 1.08rem);
  line-height: 1.58;
  margin-bottom: 1.25rem;
}

.trust-row {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
  margin-top: 1rem;

  span {
    border: 1px solid rgba(255, 255, 255, 0.14);
    border-radius: 999px;
    padding: 0.42rem 0.68rem;
    background: rgba(6, 12, 18, 0.58);
    color: #d4deea;
    font-size: 0.78rem;
  }
}

.product-frame {
  border: 1px solid rgba(255, 255, 255, 0.16);
  border-radius: 12px;
  background: rgba(9, 14, 20, 0.88);
  box-shadow: 0 24px 80px rgba(0, 0, 0, 0.42);
  overflow: hidden;
  align-self: center;
}

.frame-topbar {
  display: grid;
  grid-template-columns: 1fr auto 1fr;
  align-items: center;
  gap: 1rem;
  padding: 0.58rem 0.75rem;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);

  em {
    justify-self: end;
    color: #8ea0b4;
    font-size: 0.78rem;
    font-style: normal;
  }
}

.window-controls {
  display: inline-flex;
  gap: 0.35rem;

  span {
    width: 0.62rem;
    height: 0.62rem;
    border-radius: 999px;
    background: #334155;
  }
}

.frame-body {
  display: grid;
  grid-template-columns: 136px minmax(0, 1fr);
  min-height: 360px;
}

.mock-sidebar {
  display: flex;
  flex-direction: column;
  gap: 0.35rem;
  padding: 0.8rem 0.7rem;
  border-right: 1px solid rgba(255, 255, 255, 0.1);
  background: #0f1724;

  img {
    width: 1.65rem;
    height: 1.65rem;
    margin-bottom: 0.55rem;
  }

  span {
    border-radius: 7px;
    padding: 0.48rem 0.58rem;
    color: #8ea0b4;
    font-size: 0.78rem;
  }

  .active {
    background: rgba(47, 111, 237, 0.2);
    color: #fff;
  }
}

.mock-main {
  padding: 0.8rem;
  min-width: 0;
}

.mock-kpis {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 0.55rem;

  div {
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: 8px;
    padding: 0.62rem;
    background: #141d29;
  }

  strong {
    display: block;
    color: #fff;
    font-size: 1.25rem;
  }

  span {
    color: #8ea0b4;
    font-size: 0.72rem;
  }
}

.mock-content {
  display: grid;
  grid-template-columns: minmax(0, 1fr) minmax(220px, 0.82fr);
  gap: 0.65rem;
  margin-top: 0.7rem;
}

.mock-card {
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 8px;
  background: #141d29;
  padding: 0.75rem;
}

.card-heading,
.report-row,
.board-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.8rem;
}

.card-heading {
  margin-bottom: 0.75rem;

  span {
    color: #8ea0b4;
    font-size: 0.75rem;
  }
}

.bar-chart {
  display: flex;
  align-items: end;
  gap: 0.45rem;
  height: 180px;
  padding: 0.4rem 0.2rem 0;

  span {
    flex: 1;
    min-width: 0.7rem;
    border-radius: 5px 5px 0 0;
    background: #2f6fed;
  }
}

.board-row {
  border-top: 1px solid rgba(255, 255, 255, 0.08);
  padding: 0.64rem 0;
  color: #d4deea;

  b,
  span,
  em {
    min-width: 0;
  }

  span {
    color: #8ea0b4;
  }

  em {
    color: #85e6d2;
    font-style: normal;
    font-size: 0.76rem;
  }

  .warn {
    color: #f7c56d;
  }
}

.module-section,
.workflow-section,
.split-section,
.role-section,
.cta-section {
  padding: clamp(4rem, 8vw, 6.5rem) clamp(1rem, 4vw, 4rem);
}

.section-title {
  max-width: 760px;
  margin-bottom: 2rem;

  h2 {
    color: #fff;
    font-size: clamp(2rem, 4vw, 3.2rem);
    line-height: 1.05;
    letter-spacing: 0;
  }
}

.module-grid,
.role-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 0.9rem;
}

.module-card,
.workflow-board article,
.role-grid article,
.copy-panel,
.report-panel {
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 10px;
  background: #111923;
}

.module-card {
  padding: 1.15rem;

  h3 {
    color: #fff;
    font-size: 1rem;
    margin-bottom: 0.5rem;
  }

  p {
    color: #a8b6c6;
    font-size: 0.9rem;
    line-height: 1.58;
    margin-bottom: 0;
  }
}

.module-icon {
  width: 1.35rem;
  height: 1.35rem;
  color: #61a5ff;
  margin-bottom: 1rem;
}

.workflow-section {
  background: #0e151e;
}

.workflow-board {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 0.9rem;

  article {
    padding: 1.2rem;
  }

  span {
    display: inline-flex;
    margin-bottom: 1.25rem;
    color: #8fd7ff;
    font-weight: 800;
  }

  p {
    color: #a8b6c6;
    line-height: 1.6;
    margin-bottom: 0;
  }
}

.split-section {
  display: grid;
  grid-template-columns: minmax(0, 1fr) minmax(360px, 0.8fr);
  gap: 1rem;
}

.copy-panel,
.report-panel {
  padding: clamp(1.25rem, 3vw, 2rem);
}

.copy-panel {
  h2 {
    color: #fff;
    font-size: clamp(2rem, 4vw, 3rem);
    line-height: 1.08;
  }

  p {
    color: #a8b6c6;
    line-height: 1.72;
    max-width: 720px;
  }
}

.report-panel {
  display: grid;
  gap: 0.65rem;
}

.report-row {
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 8px;
  padding: 0.82rem 0.9rem;
  background: #0d141d;

  span {
    color: #d7e2ec;
  }

  strong {
    color: #8fd7ff;
    font-size: 0.9rem;
  }
}

.role-grid article {
  padding: 1.1rem;

  strong {
    display: block;
    color: #fff;
    margin-bottom: 0.5rem;
  }

  p {
    margin-bottom: 0;
    color: #a8b6c6;
    line-height: 1.58;
    font-size: 0.9rem;
  }
}

.cta-section {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 2rem;
  background: #0e151e;

  h2 {
    max-width: 780px;
    color: #fff;
    font-size: clamp(2rem, 4vw, 3rem);
    line-height: 1.08;
    margin-bottom: 0;
  }
}

@media (min-width: 1181px) and (max-height: 820px) {
  .hero-section {
    padding-bottom: 1rem;
  }

  .hero-grid {
    min-height: calc(100vh - 4.75rem);
  }

  .eyebrow {
    margin-bottom: 0.7rem;
  }

  h1 {
    margin-bottom: 0.85rem;
    font-size: clamp(2.45rem, 4.7vw, 4.35rem);
  }

  .lede {
    line-height: 1.48;
    margin-bottom: 1rem;
  }

  .trust-row {
    margin-top: 0.85rem;
  }

  .frame-body {
    min-height: 330px;
  }

  .mock-sidebar {
    gap: 0.25rem;

    img {
      margin-bottom: 0.3rem;
    }
  }

  .mock-kpis strong {
    font-size: 1.08rem;
  }

  .bar-chart {
    height: 155px;
  }

  .board-row {
    padding: 0.52rem 0;
  }
}

@media (max-width: 1180px) {
  .hero-grid,
  .split-section,
  .cta-section {
    grid-template-columns: 1fr;
  }

  .hero-grid {
    display: block;
  }

  .product-frame {
    margin-top: 2rem;
  }

  .module-grid,
  .workflow-board,
  .role-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (max-width: 700px) {
  .landing-nav,
  .cta-section {
    align-items: flex-start;
    flex-direction: column;
  }

  .hero-section {
    min-height: auto;
  }

  .frame-body,
  .mock-content,
  .mock-kpis,
  .module-grid,
  .workflow-board,
  .role-grid {
    grid-template-columns: 1fr;
  }

  .mock-sidebar {
    display: none;
  }

  .product-frame {
    border-radius: 10px;
  }

  .bar-chart {
    height: 170px;
  }
}
</style>
