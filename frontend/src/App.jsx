import { Link, Route, Routes } from "react-router-dom";
import { useState } from "react";
import DashboardPage from "./pages/DashboardPage";
import DocsPage from "./pages/DocsPage";
import FaqPage from "./pages/FaqPage";
import ImagePage from "./pages/ImagePage";
import SeaIcePage from "./pages/SeaIcePage";

export default function App() {
  const [faqResetToken, setFaqResetToken] = useState(0);

  return (
    <div className="app-shell">
      <header>
        <h1>
          <Link className="site-title-link" to="/">
            Weather Integration
          </Link>
        </h1>
        <nav>
          <Link to="/">Dashboard</Link>
          <Link to="/docs">Docs</Link>
          <Link to="/faq" onClick={() => setFaqResetToken((current) => current + 1)}>
            FAQ
          </Link>
        </nav>
      </header>
      <main>
        <Routes>
          <Route path="/" element={<DashboardPage />} />
          <Route path="/images/seaice_arctic" element={<SeaIcePage type="seaice_arctic" />} />
          <Route path="/images/seaice_antarctic" element={<SeaIcePage type="seaice_antarctic" />} />
          <Route path="/images/:type" element={<ImagePage />} />
          <Route path="/docs" element={<DocsPage />} />
          <Route path="/faq" element={<FaqPage resetToken={faqResetToken} />} />
        </Routes>
      </main>
    </div>
  );
}
