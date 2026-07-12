<template>
  <div class="landing-container">
    <!-- Hero Section -->
    <section class="hero-section">
      <!-- Background Effects -->
      <div class="background-effects">
        <div class="glow-primary"></div>
        <div class="glow-secondary"></div>
        <div class="glow-tertiary"></div>
      </div>

      <div class="hero-content">
        <!-- Badge -->
        <div class="version-badge">
          <span class="pulse-dot">
            <span class="ping"></span>
            <span class="dot"></span>
          </span>
          Znova v2.0 is now available
          <i class="icofont-long-arrow-right"></i>
        </div>

        <!-- Main Heading -->
        <h1 class="hero-title">
          Build Enterprise Apps with <span class="gradient-text">Znova</span>
        </h1>

        <!-- Subheading -->
        <p class="hero-subtitle">
          The modern full-stack framework combining Python FastAPI backend with Vue.js frontend. 
          Ship scalable enterprise applications with powerful metadata management and zero configuration.
        </p>

        <!-- CTA Buttons -->
        <div class="cta-group">
          <button @click="$router.push('/signup')" class="btn btn-primary">
            Get Started
            <i class="icofont-long-arrow-right"></i>
          </button>
          <button @click="$router.push('/login')" class="btn btn-secondary">
            Sign In
          </button>
        </div>

        <!-- Code Preview -->
        <div class="code-preview">
          <div class="code-window">
            <!-- Window Controls -->
            <div class="window-controls">
              <div class="control-dots">
                <span class="dot red"></span>
                <span class="dot yellow"></span>
                <span class="dot green"></span>
              </div>
              <div class="file-name">models/user.py</div>
            </div>

            <!-- Code Content -->
            <div class="code-content">
              <pre><code><span class="keyword">from</span> backend.core.znova_model <span class="keyword">import</span> ZnovaModel
<span class="keyword">from</span> backend.core <span class="keyword">import</span> fields

<span class="keyword">class</span> <span class="class-name">User</span>(ZnovaModel):
    <span class="property">__tablename__</span> = <span class="string">"users"</span>
    <span class="property">_model_name_</span> = <span class="string">"user"</span>
    
    <span class="comment"># Define fields with metadata</span>
    full_name = fields.<span class="function">Char</span>(label=<span class="string">"Full Name"</span>, required=<span class="keyword">True</span>)
    email = fields.<span class="function">Char</span>(label=<span class="string">"Email"</span>, required=<span class="keyword">True</span>)
    role_id = fields.<span class="function">Many2one</span>(<span class="string">"role"</span>, label=<span class="string">"Role"</span>)
    
    <span class="comment"># Auto-generated CRUD API + UI 🚀</span></code></pre>
            </div>
          </div>
        </div>
      </div>
    </section>

    <!-- Features Section -->
    <section class="features-section">
      <div class="section-header">
        <h2 class="section-title">Why developers choose Znova</h2>
        <p class="section-subtitle">
          Engineered for enterprise applications. We stripped away the complexity 
          so you can focus on building what matters.
        </p>
      </div>

      <div class="features-grid">
        <!-- Feature 1 -->
        <div class="feature-card">
          <div class="feature-icon-wrapper primary">
            <i class="icofont-flash"></i>
          </div>
          <h3>Rapid Development</h3>
          <p>
            Define your data models once and get auto-generated REST APIs, 
            CRUD operations, and responsive UI forms instantly.
          </p>
        </div>

        <!-- Feature 2 -->
        <div class="feature-card">
          <div class="feature-icon-wrapper purple">
            <i class="icofont-database"></i>
          </div>
          <h3>Metadata-Driven</h3>
          <p>
            Powerful metadata system with field types, validations, and domain rules. 
            Build complex business logic without writing boilerplate code.
          </p>
        </div>

        <!-- Feature 3 -->
        <div class="feature-card">
          <div class="feature-icon-wrapper cyan">
            <i class="icofont-shield-alt"></i>
          </div>
          <h3>Enterprise Security</h3>
          <p>
            Built-in role-based access control, OAuth integration, and field-level 
            permissions. Security is not an afterthought.
          </p>
        </div>

        <!-- Feature 4 -->
        <div class="feature-card">
          <div class="feature-icon-wrapper green">
            <i class="icofont-ui-browser"></i>
          </div>
          <h3>Modern UI</h3>
          <p>
            Beautiful Vue.js components with dark mode support. Responsive design 
            that works seamlessly across all devices.
          </p>
        </div>

        <!-- Feature 5 -->
        <div class="feature-card">
          <div class="feature-icon-wrapper orange">
            <i class="icofont-code-alt"></i>
          </div>
          <h3>Python + Vue.js</h3>
          <p>
            FastAPI backend for blazing-fast APIs and Vue 3 frontend with Composition API. 
            Best of both worlds in one framework.
          </p>
        </div>

        <!-- Feature 6 -->
        <div class="feature-card">
          <div class="feature-icon-wrapper pink">
            <i class="icofont-rocket-alt-2"></i>
          </div>
          <h3>Production Ready</h3>
          <p>
            Database migrations, background jobs, real-time notifications, and file uploads. 
            Everything you need to ship enterprise apps.
          </p>
        </div>
      </div>
    </section>

    <!-- Tech Stack Section -->
    <section class="tech-stack-section">
      <div class="section-header">
        <h2 class="section-title">Built with modern technologies</h2>
        <p class="section-subtitle">
          Znova combines the best tools in the ecosystem to deliver exceptional developer experience
        </p>
      </div>

      <div class="tech-grid">
        <div class="tech-item">
          <div class="tech-icon">🐍</div>
          <div class="tech-name">Python</div>
          <div class="tech-desc">FastAPI Backend</div>
        </div>
        <div class="tech-item">
          <div class="tech-icon">⚡</div>
          <div class="tech-name">Vue.js 3</div>
          <div class="tech-desc">Reactive Frontend</div>
        </div>
        <div class="tech-item">
          <div class="tech-icon">🗄️</div>
          <div class="tech-name">PostgreSQL</div>
          <div class="tech-desc">Reliable Database</div>
        </div>
        <div class="tech-item">
          <div class="tech-icon">🔐</div>
          <div class="tech-name">OAuth 2.0</div>
          <div class="tech-desc">Secure Auth</div>
        </div>
      </div>
    </section>

    <!-- CTA Section -->
    <section class="cta-section">
      <div class="cta-content">
        <h2>Ready to build your next enterprise app?</h2>
        <p>Join developers building scalable applications with Znova</p>
        <div class="cta-actions">
          <button @click="$router.push('/signup')" class="btn btn-primary btn-large">
            Start Building Now
            <i class="icofont-long-arrow-right"></i>
          </button>
          <button @click="$router.push('/login')" class="btn btn-outline btn-large">
            View Documentation
          </button>
        </div>
      </div>
    </section>

    <!-- Footer -->
    <footer class="landing-footer">
      <div class="footer-content">
        <div class="footer-brand">
          <img :src="logoText" alt="Znova" class="footer-logo" />
          <p>
            Making enterprise development faster, safer, and more enjoyable. 
            Open source and community driven.
          </p>
        </div>

        <div class="footer-links">
          <div class="footer-column">
            <h4>Product</h4>
            <ul>
              <li><a href="#">Features</a></li>
              <li><a href="#">Documentation</a></li>
              <li><a href="#">Templates</a></li>
              <li><a href="#">Enterprise</a></li>
            </ul>
          </div>

          <div class="footer-column">
            <h4>Resources</h4>
            <ul>
              <li><a href="#">API Reference</a></li>
              <li><a href="#">Community</a></li>
              <li><a href="#">Blog</a></li>
              <li><a href="#">Tutorials</a></li>
            </ul>
          </div>

          <div class="footer-column">
            <h4>Company</h4>
            <ul>
              <li><a href="#">About</a></li>
              <li><a href="#">Careers</a></li>
              <li><a href="#">Legal</a></li>
              <li><a href="#">Contact</a></li>
            </ul>
          </div>
        </div>
      </div>

      <div class="footer-bottom">
        <p>© 2024 Znova. All rights reserved.</p>
        <div class="status-indicator">
          <span class="status-dot"></span>
          Systems Operational
        </div>
      </div>
    </footer>
  </div>
</template>

<script setup lang="ts">
import logoText from '@/assets/znova_text_no_bg.png';
</script>

<style lang="scss" scoped>
@use "../styles/variables" as v;

.landing-container {
  min-height: 100vh;
  background: #0d1117;
  overflow-x: hidden;
}

// Hero Section
.hero-section {
  position: relative;
  min-height: 100vh;
  display: flex;
  align-items: center;
  padding: 8rem 2rem 4rem;
  overflow: hidden;
  
  @media (max-width: 768px) {
    padding: 6rem 1rem 3rem;
  }
}

.background-effects {
  position: absolute;
  top: 0;
  left: 50%;
  transform: translateX(-50%);
  width: 100%;
  max-width: 1400px;
  height: 100%;
  pointer-events: none;
}

.glow-primary {
  position: absolute;
  top: -10%;
  left: 25%;
  width: 500px;
  height: 500px;
  background: radial-gradient(circle, rgba(37, 99, 235, 0.2) 0%, transparent 70%);
  filter: blur(80px);
  animation: float 20s ease-in-out infinite;
}

.glow-secondary {
  position: absolute;
  top: 20%;
  right: 20%;
  width: 400px;
  height: 400px;
  background: radial-gradient(circle, rgba(168, 85, 247, 0.15) 0%, transparent 70%);
  filter: blur(70px);
  animation: float 15s ease-in-out infinite reverse;
}

.glow-tertiary {
  position: absolute;
  top: 10%;
  right: 30%;
  width: 300px;
  height: 300px;
  background: radial-gradient(circle, rgba(6, 182, 212, 0.1) 0%, transparent 70%);
  filter: blur(60px);
  animation: float 18s ease-in-out infinite;
}

@keyframes float {
  0%, 100% { transform: translateY(0px); }
  50% { transform: translateY(-30px); }
}

.hero-content {
  position: relative;
  max-width: 1200px;
  margin: 0 auto;
  text-align: center;
  z-index: 1;
}

.version-badge {
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.5rem 1rem;
  border-radius: 9999px;
  background: rgba(37, 99, 235, 0.1);
  border: 1px solid rgba(37, 99, 235, 0.2);
  color: #58a6ff;
  font-size: 0.875rem;
  font-weight: 500;
  margin-bottom: 2rem;
  cursor: pointer;
  transition: all 0.3s ease;
  
  &:hover {
    background: rgba(37, 99, 235, 0.2);
  }
  
  i {
    font-size: 0.75rem;
  }
}

.pulse-dot {
  position: relative;
  display: flex;
  align-items: center;
  justify-content: center;
  width: 8px;
  height: 8px;
}

.ping {
  position: absolute;
  width: 100%;
  height: 100%;
  border-radius: 50%;
  background: #58a6ff;
  opacity: 0.75;
  animation: ping 1.5s cubic-bezier(0, 0, 0.2, 1) infinite;
}

.dot {
  position: relative;
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #58a6ff;
}

@keyframes ping {
  75%, 100% {
    transform: scale(2);
    opacity: 0;
  }
}

.hero-title {
  font-size: clamp(2.5rem, 8vw, 4.5rem);
  font-weight: 700;
  line-height: 1.1;
  margin-bottom: 1.5rem;
  color: #e6edf3;
  letter-spacing: -0.02em;
}

.gradient-text {
  background: linear-gradient(135deg, #2563eb 0%, #7c3aed 50%, #06b6d4 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.hero-subtitle {
  font-size: clamp(1.125rem, 2vw, 1.25rem);
  color: #7d8590;
  max-width: 700px;
  margin: 0 auto 2.5rem;
  line-height: 1.6;
}

.cta-group {
  display: flex;
  gap: 1rem;
  justify-content: center;
  margin-bottom: 4rem;
  flex-wrap: wrap;
  
  @media (max-width: 480px) {
    flex-direction: column;
    align-items: center;
  }
}

.btn {
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.875rem 2rem;
  border-radius: 0.5rem;
  font-weight: 600;
  font-size: 1rem;
  cursor: pointer;
  transition: all 0.3s ease;
  border: none;
  
  &.btn-large {
    padding: 1rem 2.5rem;
    font-size: 1.125rem;
  }
  
  &.btn-primary {
    background: #2563eb;
    color: white;
    box-shadow: 0 0 20px rgba(37, 99, 235, 0.3);
    
    &:hover {
      background: #1d4ed8;
      box-shadow: 0 0 30px rgba(37, 99, 235, 0.5);
      transform: translateY(-2px);
    }
    
    i {
      transition: transform 0.3s ease;
    }
    
    &:hover i {
      transform: translateX(4px);
    }
  }
  
  &.btn-secondary {
    background: rgba(48, 54, 61, 0.6);
    color: #e6edf3;
    border: 1px solid #30363d;
    
    &:hover {
      background: rgba(48, 54, 61, 0.8);
      border-color: #484f58;
      transform: translateY(-2px);
    }
  }
  
  &.btn-outline {
    background: transparent;
    color: #e6edf3;
    border: 2px solid #58a6ff;
    
    &:hover {
      background: #58a6ff;
      color: #0d1117;
      transform: translateY(-2px);
    }
  }
}

// Code Preview
.code-preview {
  max-width: 900px;
  margin: 0 auto;
  perspective: 1000px;
}

.code-window {
  position: relative;
  background: #0d0d16;
  border: 1px solid #30363d;
  border-radius: 0.75rem;
  overflow: hidden;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.5);
  transition: transform 0.7s ease;
  
  &:hover {
    transform: rotateX(0deg);
  }
  
  &::before {
    content: '';
    position: absolute;
    inset: -1px;
    background: linear-gradient(135deg, rgba(37, 99, 235, 0.2), transparent, rgba(168, 85, 247, 0.2));
    opacity: 0.2;
    filter: blur(20px);
    z-index: -1;
  }
}

.window-controls {
  display: flex;
  align-items: center;
  gap: 1rem;
  padding: 0.75rem 1rem;
  background: rgba(255, 255, 255, 0.03);
  border-bottom: 1px solid rgba(255, 255, 255, 0.05);
}

.control-dots {
  display: flex;
  gap: 0.5rem;
}

.control-dots .dot {
  width: 12px;
  height: 12px;
  border-radius: 50%;
  
  &.red { background: rgba(255, 95, 86, 0.8); }
  &.yellow { background: rgba(255, 189, 46, 0.8); }
  &.green { background: rgba(40, 201, 64, 0.8); }
}

.file-name {
  font-family: 'Courier New', monospace;
  font-size: 0.75rem;
  color: #7d8590;
}

.code-content {
  padding: 1.5rem;
  overflow-x: auto;
  
  pre {
    margin: 0;
    font-family: 'Courier New', monospace;
    font-size: 0.875rem;
    line-height: 1.6;
    color: #e6edf3;
    text-align: left;
  }
  
  .keyword { color: #ff79c6; }
  .function { color: #8be9fd; }
  .string { color: #f1fa8c; }
  .comment { color: #6272a4; font-style: italic; }
  .class-name { color: #50fa7b; }
  .property { color: #bd93f9; }
}

// Features Section
.features-section {
  padding: 6rem 2rem;
  background: #161b22;
  
  @media (max-width: 768px) {
    padding: 4rem 1rem;
  }
}

.section-header {
  max-width: 800px;
  margin: 0 auto 4rem;
  text-align: center;
}

.section-title {
  font-size: clamp(2rem, 5vw, 2.5rem);
  font-weight: 700;
  color: #e6edf3;
  margin-bottom: 1rem;
}

.section-subtitle {
  font-size: 1.125rem;
  color: #7d8590;
  line-height: 1.6;
}

.features-grid {
  max-width: 1200px;
  margin: 0 auto;
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: 2rem;
  
  @media (max-width: 768px) {
    grid-template-columns: 1fr;
  }
}

.feature-card {
  padding: 2rem;
  background: rgba(13, 17, 23, 0.7);
  backdrop-filter: blur(20px);
  border: 1px solid #30363d;
  border-radius: 0.75rem;
  transition: all 0.3s ease;
  position: relative;
  overflow: hidden;
  
  &:hover {
    border-color: #58a6ff;
    box-shadow: 0 0 30px rgba(88, 166, 255, 0.15);
    transform: translateY(-5px);
  }
  
  h3 {
    font-size: 1.25rem;
    font-weight: 600;
    color: #e6edf3;
    margin-bottom: 0.75rem;
  }
  
  p {
    color: #7d8590;
    line-height: 1.6;
    font-size: 0.9375rem;
  }
}

.feature-icon-wrapper {
  width: 48px;
  height: 48px;
  border-radius: 0.5rem;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 1.5rem;
  transition: transform 0.3s ease;
  
  i {
    font-size: 1.5rem;
  }
  
  &.primary {
    background: rgba(37, 99, 235, 0.1);
    color: #58a6ff;
  }
  
  &.purple {
    background: rgba(168, 85, 247, 0.1);
    color: #a78bfa;
  }
  
  &.cyan {
    background: rgba(6, 182, 212, 0.1);
    color: #22d3ee;
  }
  
  &.green {
    background: rgba(63, 185, 80, 0.1);
    color: #3fb950;
  }
  
  &.orange {
    background: rgba(251, 146, 60, 0.1);
    color: #fb923c;
  }
  
  &.pink {
    background: rgba(236, 72, 153, 0.1);
    color: #ec4899;
  }
  
  .feature-card:hover & {
    transform: scale(1.1);
  }
}

// Tech Stack Section
.tech-stack-section {
  padding: 6rem 2rem;
  background: #0d1117;
  border-top: 1px solid #30363d;
  
  @media (max-width: 768px) {
    padding: 4rem 1rem;
  }
}

.tech-grid {
  max-width: 900px;
  margin: 0 auto;
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 2rem;
  
  @media (max-width: 768px) {
    grid-template-columns: repeat(2, 1fr);
  }
}

.tech-item {
  text-align: center;
  padding: 2rem 1rem;
  background: rgba(22, 27, 34, 0.5);
  border: 1px solid #30363d;
  border-radius: 0.75rem;
  transition: all 0.3s ease;
  
  &:hover {
    border-color: #484f58;
    transform: translateY(-5px);
  }
}

.tech-icon {
  font-size: 3rem;
  margin-bottom: 1rem;
}

.tech-name {
  font-size: 1.125rem;
  font-weight: 600;
  color: #e6edf3;
  margin-bottom: 0.5rem;
}

.tech-desc {
  font-size: 0.875rem;
  color: #7d8590;
}

// CTA Section
.cta-section {
  padding: 6rem 2rem;
  background: linear-gradient(135deg, #0d1117 0%, #161b22 100%);
  border-top: 1px solid #30363d;
  text-align: center;
  
  @media (max-width: 768px) {
    padding: 4rem 1rem;
  }
}

.cta-content {
  max-width: 800px;
  margin: 0 auto;
  
  h2 {
    font-size: clamp(2rem, 5vw, 2.5rem);
    font-weight: 700;
    color: #e6edf3;
    margin-bottom: 1rem;
  }
  
  p {
    font-size: 1.25rem;
    color: #7d8590;
    margin-bottom: 2.5rem;
  }
}

.cta-actions {
  display: flex;
  gap: 1rem;
  justify-content: center;
  flex-wrap: wrap;
  
  @media (max-width: 480px) {
    flex-direction: column;
    align-items: center;
  }
}

// Footer
.landing-footer {
  background: #0d1117;
  border-top: 1px solid #30363d;
  padding: 4rem 2rem 2rem;
  
  @media (max-width: 768px) {
    padding: 3rem 1rem 1.5rem;
  }
}

.footer-content {
  max-width: 1200px;
  margin: 0 auto 3rem;
  display: grid;
  grid-template-columns: 2fr 3fr;
  gap: 4rem;
  
  @media (max-width: 768px) {
    grid-template-columns: 1fr;
    gap: 2rem;
  }
}

.footer-brand {
  .footer-logo {
    height: 32px;
    width: auto;
    margin-bottom: 1rem;
  }
  
  p {
    color: #7d8590;
    font-size: 0.9375rem;
    line-height: 1.6;
    max-width: 400px;
  }
}

.footer-links {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 2rem;
  
  @media (max-width: 480px) {
    grid-template-columns: 1fr;
  }
}

.footer-column {
  h4 {
    color: #e6edf3;
    font-weight: 600;
    margin-bottom: 1rem;
    font-size: 0.9375rem;
  }
  
  ul {
    list-style: none;
    padding: 0;
    margin: 0;
  }
  
  li {
    margin-bottom: 0.75rem;
  }
  
  a {
    color: #7d8590;
    text-decoration: none;
    font-size: 0.875rem;
    transition: color 0.3s ease;
    
    &:hover {
      color: #58a6ff;
    }
  }
}

.footer-bottom {
  max-width: 1200px;
  margin: 0 auto;
  padding-top: 2rem;
  border-top: 1px solid #30363d;
  display: flex;
  justify-content: space-between;
  align-items: center;
  
  @media (max-width: 768px) {
    flex-direction: column;
    gap: 1rem;
    text-align: center;
  }
  
  p {
    color: #7d8590;
    font-size: 0.875rem;
    margin: 0;
  }
}

.status-indicator {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  color: #7d8590;
  font-size: 0.875rem;
}

.status-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #3fb950;
  box-shadow: 0 0 10px rgba(63, 185, 80, 0.5);
}
</style>
