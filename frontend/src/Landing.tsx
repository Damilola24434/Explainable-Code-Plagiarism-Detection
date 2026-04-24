/*
This file is basically the landing page for our plagiarism detection system. 
It is the first thing the user sees before they actually go into the main app. 
So the goal of this file is to explain what the system does, how to use it, 
and also guide the user step by step in a simple way.

At the top, we import things like useEffect, the CSS file for styling, 
and also images for the team members. These images are used later in the 
team section to show who worked on the project. :contentReference[oaicite:0]{index=0}

Then we define the Landing component, which takes a function called 
onGetStarted. This function is used when the user clicks buttons like 
"Get Started" or "Launch App" to move them into the main system.

Inside the component, there is a useEffect hook. This part is used to 
handle animations when the user scrolls. It uses something called 
IntersectionObserver to check when elements like cards (steps, requirements, 
team, features) come into view. When they show on the screen, a "visible" 
class is added so animations can happen. This just makes the UI look nicer 
and more modern.

There is also a helper function called scrollToSection. This is used for 
navigation. When the user clicks something like "About" or "How to Use", 
the page smoothly scrolls to that section instead of jumping.

The return part is the main layout of the page.

First, we have the navbar. This includes:
- The title "Plagiarism Detector" on the left
- Navigation links in the center (Home, About, How to Use, Requirements, Team)
- A "Launch App" button on the right

Next is the hero section. This is like the main introduction. It shows 
the system name, a short description, and buttons like "Get Started" 
and "Learn More".

After that, we have the About section. This explains what the system does. 
It talks about things like similarity analysis, result visualization, 
and academic integrity. Basically why this system is useful.

Then we have the How to Use section. This shows a simple 4-step process:
1. Create a collection
2. Upload student files
3. Start analysis
4. View results

After that is the Requirements section. This tells the user what kind of 
files are supported (Python, Java, C++, JavaScript), and what is needed 
for the system to work properly like a browser and internet.

Then there is the File Structure section. This shows how student files 
should be named and organized. This helps the system process everything 
correctly.

Next is the Team section. This shows each team member, their role, and 
what they worked on. For example, similarity detection, AST analysis, 
and system integration.

After that is the Acknowledgement section. This gives credit to people 
like the client and domain expert who helped guide the project.

Finally, there is the footer at the bottom with the project name and 
a small message.

Overall, this file is mainly for UI and user experience. It does not do 
the actual plagiarism detection, but it explains everything and helps 
users navigate before using the system.
*/
import { useEffect } from "react";
import "./landing.css";
import damilolaImg from "./assets/Damilola.jpeg";
import gabeImg from "./assets/Gabriella.png";
import toluImg from "./assets/Tolu.png";

interface LandingProps {
  onGetStarted: () => void;
}

export default function Landing({ onGetStarted }: LandingProps) {
  useEffect(() => {
    // Intersection observer for scroll animations
    const observerOptions = {
      threshold: 0.1,
      rootMargin: "0px 0px -100px 0px",
    };

    const observer = new IntersectionObserver((entries) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) {
          entry.target.classList.add("visible");
        }
      });
    }, observerOptions);

    document.querySelectorAll(".step-card, .req-card, .team-card, .feature-item").forEach((card) => {
      observer.observe(card);
    });

    return () => observer.disconnect();
  }, []);

  const scrollToSection = (id: string) => {
    const element = document.getElementById(id);
    if (element) {
      element.scrollIntoView({ behavior: "smooth", block: "start" });
    }
  };

  return (
    <div className="landing-container">
      {/* ===== NAVBAR - SAME AS MAIN APP ===== */}
      <nav className="site-nav navbar">
        <div className="site-nav-inner">
          <div className="nav-left">
            <button type="button" className="site-title brand-link">
              Plagiarism Detector
            </button>
          </div>

 <nav className="nav-center" aria-label="Page navigation">
  <div className="nav-links">
    <button type="button" className="nav-link">
  Home
</button>
    <button type="button" className="nav-link" onClick={() => scrollToSection("about")}>
      About
    </button>

    <button type="button" className="nav-link" onClick={() => scrollToSection("how-to-use")}>
      How to Use
    </button>

    <button type="button" className="nav-link" onClick={() => scrollToSection("requirements")}>
      Requirements
    </button>

    <button type="button" className="nav-link" onClick={() => scrollToSection("team")}>
      Team
    </button>
  </div>
</nav>
          <div className="nav-right">
            <button onClick={onGetStarted} className="nav-cta">
              Launch App
            </button>
          </div>
        </div>
      </nav>

      {/* ===== HERO SECTION ===== */}
      <section className="hero">
        <div className="hero-content">
          <h1>Code Plagiarism Detection System</h1>
          <p>Intelligent similarity detection for student code submissions.</p>
          <div className="hero-buttons">
            <button onClick={onGetStarted} className="btn btn-primary">
              Get Started
            </button>
            <button onClick={() => scrollToSection("about")} className="btn btn-secondary">
              Learn More
            </button>
          </div>
        </div>
      </section>

      {/* ===== ABOUT SECTION ===== */}
      <section className="about" id="about">
        <div className="container">
          <div className="section-header">
            <h2>About the System</h2>
          </div>
          <div className="about-content">
            <p className="about-text">
              The Code Plagiarism Detection System is a sophisticated, web-based platform designed to help educators and institutions detect code plagiarism in student submissions. Using advanced Abstract Syntax Tree (AST) analysis and machine learning techniques, our system compares student code submissions to identify similarities and potential plagiarism.
            </p>
            <div className="about-features">
              <div className="feature-item">
                <h3> Similarity Analysis</h3>
                <p>Advanced algorithms compare code submissions at multiple levels to identify structural and semantic similarities.</p>
              </div>
              <div className="feature-item">
                <h3> Result Visualization</h3>
                <p>Interactive dashboards and detailed reports make it easy to understand and review plagiarism detection results.</p>
              </div>
              <div className="feature-item">
                <h3> Academic Integrity</h3>
                <p>Maintain academic standards and ensure fair evaluation through comprehensive plagiarism detection and evidence reporting.</p>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* ===== HOW TO USE SECTION ===== */}
      <section className="how-to-use" id="how-to-use">
        <div className="container">
          <div className="section-header">
            <h2>How to Use</h2>
            <p>Simple 4-step process to detect plagiarism</p>
          </div>
          <div className="steps-grid">
            <div className="step-card" data-step="1">
              <h3>Create a Collection</h3>
              <p>Start by creating a new collection for your assignment or course. Give it a descriptive name and optional description.</p>
            </div>
            <div className="step-card" data-step="2">
              <h3>Upload Student Files</h3>
              <p>Upload all student code submissions in supported formats (Python, Java, C++, JavaScript). Files should be properly named.</p>
            </div>
            <div className="step-card" data-step="3">
              <h3>Start Analysis</h3>
              <p>Initiate the plagiarism detection process. The system will analyze all submissions and compute similarity scores.</p>
            </div>
            <div className="step-card" data-step="4">
              <h3>View Similarity Results</h3>
              <p>Review detailed reports showing similarity pairs, evidence snippets, and visualization of potential plagiarism.</p>
            </div>
          </div>
        </div>
      </section>

      {/* ===== REQUIREMENTS SECTION ===== */}
      <section className="requirements" id="requirements">
        <div className="container">
          <div className="section-header">
            <h2>Requirements</h2>
            <p>What you need to get started</p>
          </div>
          <div className="req-grid">
            <div className="req-card">
              <h3> Supported File Types</h3>
              <ul>
                <li>Python (.py)</li>
                <li>Java (.java)</li>
                <li>C++ (.cpp)</li>
                <li>JavaScript (.js)</li>
              </ul>
            </div>
            <div className="req-card">
              <h3> File Requirements</h3>
              <ul>
                <li>Well-formed source code</li>
                <li>No corrupted or binary files</li>
                <li>Text-based code files only</li>
                <li>Reasonable file sizes</li>
              </ul>
            </div>
            <div className="req-card">
              <h3> System Requirements</h3>
              <ul>
                <li>Modern web browser</li>
                <li>Stable internet connection</li>
                <li>JavaScript enabled</li>
                <li>Cookies enabled for sessions</li>
              </ul>
            </div>
          </div>
        </div>
      </section>

      {/* ===== FILE STRUCTURE SECTION ===== */}
      <section className="file-structure" id="file-structure">
        <div className="container">
          <div className="section-header">
            <h2>Expected File Structure</h2>
            <p>Organize your submissions for optimal analysis</p>
          </div>
          <div className="structure-box">
            <code>
              submission/
              <br />
              ├── student_001_assignment1.py
              <br />
              ├── student_002_assignment1.py
              <br />
              ├── student_003_assignment1.java
              <br />
              ├── student_004_assignment1.cpp
              <br />
              └── student_005_assignment1.js
            </code>
          </div>
          <div className="structure-explanation">
            <h4> Recommended Naming Convention</h4>
            <p>
              <strong>Format:</strong> <code>studentID_assignmentname.extension</code>
            </p>
            <p>
              <strong>Example:</strong> <code>student_001_assignment1.py</code>
            </p>
            <p>
              <strong>Tip:</strong> Use consistent naming patterns to make batch uploads and result analysis easier.
            </p>
          </div>
        </div>
      </section>

      {/* ===== TEAM SECTION ===== */}
<section className="team" id="team">
  <div className="container">
    <div className="section-header">
      <h2>Our Team</h2>
      <p>Meet the team behind the system</p>
    </div>

    <div className="team-grid">

      {/* MEMBER 1 */}
      <div className="team-card">
        <img src={toluImg} alt="Toluwalope Kuseju" className="avatar-img" />
        <h3>Toluwalope Kuseju</h3>
        <p className="role">Algorithmic Similarity Detection</p>
        <p>
          Designed and implemented the token-based similarity detection pipeline, 
          including k-gram generation and Winnowing fingerprinting techniques. 
          Evaluated similarity thresholds and analyzed detection accuracy to ensure reliable results.
        </p>
      </div>

      {/* MEMBER 2 */}
      <div className="team-card">
         <img src={gabeImg} alt="Gaberialla Toby" className="avatar-img" />
        <h3>Gaberialla Toby</h3>
        <p className="role">Structural Code Analysis (AST)</p>
        <p>
          Developed structural analysis using Abstract Syntax Trees (ASTs), including 
          parsing source code and implementing custom traversal and comparison logic. 
          Mapped structural similarities and differences across submissions for deeper analysis.
        </p>
      </div>

      {/* MEMBER 3 */}
      <div className="team-card">
        <img src={damilolaImg} alt="Damilola Osoba" className="avatar-img" />
        <h3>Damilola Osoba</h3>
        <p className="role">Platform Engineering & System Integration</p>
        <p>
          Led platform-level engineering, including asynchronous processing of submissions 
          and large-scale comparison jobs. Built reporting pipelines, result aggregation, 
          and visualization systems to present similarity insights effectively.
        </p>
      </div>

    </div>
  </div>
</section>

    <section className="acknowledgement" id="acknowledgement">
  <div className="container">
    <div className="ack-content">
      <h3>Acknowledgements</h3>

      <div className="ack-item">
        <strong>Client:</strong> <em>Dr. Bei Xie</em> - Project client providing requirements and domain expertise.
      </div>

      <div className="ack-item">
        <strong>Domain Expert:</strong> <em>Dr. Jennifer Lavergne</em> - Academic advisor and domain expert ensuring the system meets standards and educational requirements.
      </div>

      <div className="ack-item">
        <strong>References:</strong>
       <ul className="ack-list">
  <li>FastAPI Documentation: Backend API development and request handling.</li>
  <li>Celery Documentation (v5.6.2): Distributed task queue and background processing.</li>
  <li>Matplotlib Documentation (v3.10.8): Data visualization and result outputs.</li>
  <li>Docker Documentation: Containerization and deployment.</li>
  <li>UI/UX Design Documentation: Material Design and UI best practices.</li>
  <li>Python Tokenize Module Documentation: Token-based code analysis.</li>
  <li>Python AST Module Documentation: Structural code parsing.</li>
  <li>Tree-sitter Documentation: Syntax parsing and analysis.</li>
  <li>LLVM Clang AST Tutorials: AST traversal and comparison techniques.</li>
  <li>Stanford CS143 Notes: Lexical analysis concepts.</li>
  <li>Jurafsky & Martin: Language processing and tokenization concepts.</li>
  <li>Introduction to Algorithms (Cormen et al.): Algorithm design.</li>
  <li>ACM Digital Library: Code similarity and plagiarism research.</li>
  <li>IEEE Xplore: Program analysis and software similarity studies.</li>
  <li>Hero Image: Generated using ChatGPT (AI-generated image).</li>
</ul>
         
      </div>

    </div>
  </div>
</section>
      {/* ===== FOOTER ===== */}
      <footer className="landing-footer">
        <div className="footer-content">
        
          <p className="footer-text">Code Plagiarism Detection System</p>
          <div className="footer-credits">
            <p>Built with passion </p>
          </div>
        </div>
      </footer>
    </div>
  );
}
