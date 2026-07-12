<template>
  <main class="landing-page">
    <section class="hero">
      <div class="route-field" aria-hidden="true">
        <span class="route-line route-line-a"></span>
        <span class="route-line route-line-b"></span>
        <span class="route-node node-a"></span>
        <span class="route-node node-b"></span>
        <span class="route-node node-c"></span>
        <span class="route-node node-d"></span>
      </div>

      <nav class="landing-nav">
        <button class="brand" type="button" @click="$router.push('/')">
          <img :src="logoIcon" alt="" />
          <span>TransitOps</span>
        </button>
        <div class="nav-actions">
          <button type="button" class="text-link" @click="$router.push('/login')">Sign in</button>
          <button type="button" class="small-button" @click="$router.push('/signup')">Create account</button>
        </div>
      </nav>

      <div class="hero-content">
        <p class="eyebrow">Smart transport operations workspace</p>
        <h1>Run fleet, driver, trip, and cost operations from one role-aware system.</h1>
        <p class="hero-copy">
          TransitOps brings vehicles, regions, drivers, trips, maintenance, fuel logs, expenses, and operational
          reports into a single workspace built for dispatch teams and transport managers.
        </p>
        <div class="hero-actions">
          <button type="button" class="primary-button" @click="$router.push('/signup')">Start operations</button>
          <button type="button" class="secondary-button" @click="$router.push('/login')">Open dashboard</button>
        </div>
      </div>

      <div class="ops-preview" aria-label="TransitOps operations snapshot">
        <div class="preview-header">
          <div>
            <span class="preview-label">Live board</span>
            <strong>Fleet Control</strong>
          </div>
          <span class="status-pill">Operational</span>
        </div>
        <div class="metric-strip">
          <div>
            <span>Vehicles</span>
            <strong>48</strong>
          </div>
          <div>
            <span>Active trips</span>
            <strong>17</strong>
          </div>
          <div>
            <span>In shop</span>
            <strong>04</strong>
          </div>
        </div>
        <div class="dispatch-row">
          <span class="vehicle-dot"></span>
          <div>
            <strong>TRK-2049</strong>
            <span>West Zone to Central Hub</span>
          </div>
          <em>Dispatched</em>
        </div>
        <div class="dispatch-row">
          <span class="vehicle-dot muted"></span>
          <div>
            <strong>VAN-1182</strong>
            <span>North Depot to Airport</span>
          </div>
          <em>Draft</em>
        </div>
      </div>
    </section>

    <section class="workflow-section">
      <div class="section-heading">
        <p class="eyebrow">Built around the daily flow</p>
        <h2>Plan, dispatch, maintain, and measure every transport operation.</h2>
      </div>

      <div class="workflow-grid">
        <article>
          <span>01</span>
          <h3>Prepare master data</h3>
          <p>Seed regions, register vehicles, keep driver records clean, and control access by operational role.</p>
        </article>
        <article>
          <span>02</span>
          <h3>Dispatch trips</h3>
          <p>Assign available vehicles and eligible drivers, then move trips through draft, dispatched, completed, or cancelled states.</p>
        </article>
        <article>
          <span>03</span>
          <h3>Track cost and service</h3>
          <p>Capture maintenance, fuel, and expenses so managers can see operating cost and utilization trends.</p>
        </article>
      </div>
    </section>

    <section class="capabilities-section">
      <div class="capability-panel">
        <div class="section-heading compact">
          <p class="eyebrow">Core modules</p>
          <h2>Everything the TransitOps spec needs, organized by role.</h2>
        </div>
        <div class="capability-list">
          <span>Vehicles</span>
          <span>Regions</span>
          <span>Driver Directory</span>
          <span>Trip Board</span>
          <span>Maintenance Log</span>
          <span>Fuel Logs</span>
          <span>Expenses</span>
          <span>Reports</span>
        </div>
      </div>

      <div class="role-panel">
        <h3>Role-aware by default</h3>
        <ul>
          <li>Admin manages users, roles, setup, and unlocks.</li>
          <li>Fleet Manager owns fleet, regions, maintenance, and trip operations.</li>
          <li>Driver works from assigned and own trips.</li>
          <li>Safety Officer focuses on driver compliance.</li>
          <li>Financial Analyst owns fuel, expenses, and cost reporting.</li>
        </ul>
      </div>
    </section>

    <section class="final-cta">
      <h2>Ready to manage the fleet workspace?</h2>
      <p>Use the seeded admin account, invite operational users, and continue building the trip engine from the spec.</p>
      <div class="hero-actions">
        <button type="button" class="primary-button" @click="$router.push('/login')">Sign in</button>
        <button type="button" class="secondary-button" @click="$router.push('/signup')">Create operational user</button>
      </div>
    </section>
  </main>
</template>

<script setup lang="ts">
import logoIcon from '../assets/transitops_mark.svg';
</script>

<style lang="scss" scoped>
.landing-page {
  min-height: 100vh;
  background: #090d12;
  color: #eef4fb;
}

.hero {
  position: relative;
  min-height: 92vh;
  overflow: hidden;
  padding: 1.25rem clamp(1rem, 4vw, 4rem) 3rem;
  background:
    linear-gradient(110deg, rgba(9, 13, 18, 0.96) 0%, rgba(9, 13, 18, 0.86) 48%, rgba(10, 24, 33, 0.72) 100%),
    linear-gradient(180deg, #10202a 0%, #090d12 100%);
}

.route-field {
  position: absolute;
  inset: 0;
  opacity: 0.7;
  background-image:
    linear-gradient(rgba(120, 152, 171, 0.08) 1px, transparent 1px),
    linear-gradient(90deg, rgba(120, 152, 171, 0.08) 1px, transparent 1px);
  background-size: 56px 56px;
}

.route-line {
  position: absolute;
  height: 2px;
  background: linear-gradient(90deg, transparent, #2f80ed, #41c7b9, transparent);
  transform-origin: left center;
}

.route-line-a {
  width: 56vw;
  right: 3vw;
  top: 34%;
  transform: rotate(-18deg);
}

.route-line-b {
  width: 44vw;
  right: 12vw;
  top: 62%;
  transform: rotate(17deg);
}

.route-node {
  position: absolute;
  width: 0.875rem;
  height: 0.875rem;
  border: 2px solid #7dd3fc;
  border-radius: 999px;
  background: #0b1220;
  box-shadow: 0 0 0 6px rgba(45, 127, 237, 0.14);
}

.node-a { right: 36%; top: 28%; }
.node-b { right: 12%; top: 43%; }
.node-c { right: 31%; top: 67%; }
.node-d { right: 7%; top: 58%; }

.landing-nav {
  position: relative;
  z-index: 2;
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
  color: #ffffff;
  font: inherit;
  font-size: 1.125rem;
  font-weight: 750;
  cursor: pointer;

  img {
    width: 2rem;
    height: 2rem;
  }
}

.nav-actions,
.hero-actions {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  flex-wrap: wrap;
}

button {
  font: inherit;
}

.text-link {
  border: 0;
  background: transparent;
  color: #b9c5d1;
  cursor: pointer;
}

.small-button,
.primary-button,
.secondary-button {
  border-radius: 0.5rem;
  cursor: pointer;
  transition: border-color 0.2s ease, background 0.2s ease, transform 0.2s ease;
}

.small-button {
  padding: 0.65rem 1rem;
  border: 1px solid rgba(255, 255, 255, 0.16);
  background: rgba(255, 255, 255, 0.08);
  color: #ffffff;
}

.primary-button,
.secondary-button {
  min-height: 3rem;
  padding: 0.85rem 1.3rem;
  border: 1px solid transparent;
  font-weight: 700;
}

.primary-button {
  background: #2f80ed;
  color: #ffffff;
  box-shadow: 0 16px 34px rgba(47, 128, 237, 0.25);
}

.secondary-button {
  background: rgba(255, 255, 255, 0.08);
  border-color: rgba(255, 255, 255, 0.16);
  color: #e5edf5;
}

.small-button:hover,
.primary-button:hover,
.secondary-button:hover {
  transform: translateY(-1px);
}

.hero-content {
  position: relative;
  z-index: 1;
  max-width: 760px;
  padding-top: clamp(5rem, 12vh, 8rem);
}

.eyebrow {
  margin: 0 0 1rem;
  color: #7dd3fc;
  font-size: 0.78rem;
  font-weight: 800;
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
  margin-bottom: 1.25rem;
  max-width: 850px;
  font-size: clamp(2.7rem, 7vw, 5.6rem);
  line-height: 0.98;
  letter-spacing: 0;
}

.hero-copy {
  max-width: 650px;
  margin-bottom: 2rem;
  color: #b9c5d1;
  font-size: clamp(1rem, 2vw, 1.2rem);
  line-height: 1.7;
}

.ops-preview {
  position: relative;
  z-index: 1;
  width: min(100%, 760px);
  margin-top: clamp(2.5rem, 9vh, 5rem);
  border: 1px solid rgba(255, 255, 255, 0.12);
  border-radius: 0.5rem;
  background: rgba(12, 18, 26, 0.82);
  box-shadow: 0 24px 80px rgba(0, 0, 0, 0.3);
  backdrop-filter: blur(16px);
}

.preview-header,
.metric-strip,
.dispatch-row {
  display: flex;
  align-items: center;
}

.preview-header {
  justify-content: space-between;
  padding: 1rem;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
}

.preview-label,
.metric-strip span,
.dispatch-row span,
.role-panel li,
.final-cta p {
  color: #92a2b3;
}

.preview-header strong {
  display: block;
  margin-top: 0.2rem;
}

.status-pill {
  border-radius: 999px;
  padding: 0.35rem 0.7rem;
  background: rgba(65, 199, 185, 0.14);
  color: #7ee4d8;
  font-size: 0.8rem;
  font-weight: 700;
}

.metric-strip {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);

  div {
    padding: 1rem;
    border-right: 1px solid rgba(255, 255, 255, 0.1);
  }

  div:last-child {
    border-right: 0;
  }

  strong {
    display: block;
    margin-top: 0.25rem;
    font-size: 1.6rem;
  }
}

.dispatch-row {
  gap: 0.85rem;
  padding: 1rem;
  border-bottom: 1px solid rgba(255, 255, 255, 0.08);

  div {
    flex: 1;
    min-width: 0;
  }

  strong,
  span {
    display: block;
  }

  em {
    color: #7dd3fc;
    font-style: normal;
    font-size: 0.875rem;
  }
}

.dispatch-row:last-child {
  border-bottom: 0;
}

.vehicle-dot {
  width: 0.75rem;
  height: 0.75rem;
  border-radius: 999px;
  background: #41c7b9;
  flex: 0 0 auto;
}

.vehicle-dot.muted {
  background: #f4bf50;
}

.workflow-section,
.capabilities-section,
.final-cta {
  padding: clamp(4rem, 9vw, 7rem) clamp(1rem, 4vw, 4rem);
}

.section-heading {
  max-width: 760px;
  margin-bottom: 2rem;

  h2 {
    color: #f6f9fc;
    font-size: clamp(2rem, 4vw, 3.1rem);
    line-height: 1.08;
    letter-spacing: 0;
  }
}

.section-heading.compact {
  margin-bottom: 1.5rem;
}

.workflow-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 1rem;
}

.workflow-grid article,
.capability-panel,
.role-panel {
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 0.5rem;
  background: #111821;
}

.workflow-grid article {
  padding: 1.4rem;

  span {
    display: inline-flex;
    margin-bottom: 1.5rem;
    color: #7dd3fc;
    font-weight: 800;
  }

  h3 {
    color: #ffffff;
    font-size: 1.2rem;
  }

  p {
    margin-bottom: 0;
    color: #9dadbe;
    line-height: 1.65;
  }
}

.capabilities-section {
  display: grid;
  grid-template-columns: minmax(0, 1.4fr) minmax(280px, 0.6fr);
  gap: 1rem;
  background: #0c1118;
}

.capability-panel,
.role-panel {
  padding: clamp(1.25rem, 3vw, 2rem);
}

.capability-list {
  display: flex;
  flex-wrap: wrap;
  gap: 0.75rem;

  span {
    border: 1px solid rgba(125, 211, 252, 0.18);
    border-radius: 999px;
    padding: 0.65rem 0.9rem;
    background: rgba(125, 211, 252, 0.08);
    color: #dceeff;
    font-size: 0.95rem;
  }
}

.role-panel {
  h3 {
    color: #ffffff;
    font-size: 1.3rem;
  }

  ul {
    margin: 0;
    padding-left: 1.1rem;
  }

  li {
    margin-bottom: 0.8rem;
    line-height: 1.55;
  }
}

.final-cta {
  text-align: center;

  h2 {
    margin-bottom: 0.75rem;
    color: #ffffff;
    font-size: clamp(2rem, 4vw, 3rem);
  }

  p {
    max-width: 680px;
    margin: 0 auto 1.5rem;
    line-height: 1.7;
  }

  .hero-actions {
    justify-content: center;
  }
}

@media (max-width: 900px) {
  .workflow-grid,
  .capabilities-section {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 640px) {
  .landing-nav {
    align-items: flex-start;
  }

  .nav-actions {
    justify-content: flex-end;
  }

  .hero {
    min-height: auto;
  }

  .metric-strip {
    grid-template-columns: 1fr;

    div {
      border-right: 0;
      border-bottom: 1px solid rgba(255, 255, 255, 0.1);
    }

    div:last-child {
      border-bottom: 0;
    }
  }

  .dispatch-row {
    align-items: flex-start;

    em {
      display: none;
    }
  }
}
</style>
