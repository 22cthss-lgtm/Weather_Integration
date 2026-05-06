import { Link, Route, Routes } from "react-router-dom";
import DashboardPage from "./pages/DashboardPage";
import DocsPage from "./pages/DocsPage";
import ImagePage from "./pages/ImagePage";

export default function App() {
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
        </nav>
      </header>
      <main>
        <Routes>
          <Route path="/" element={<DashboardPage />} />
          <Route path="/images/:type" element={<ImagePage />} />
          <Route path="/docs" element={<DocsPage />} />
        </Routes>
      </main>
    </div>
  );
}
