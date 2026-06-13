import { AnimatePresence } from "framer-motion";
import { Route, Routes, useLocation } from "react-router-dom";
import Layout from "./components/Layout";
import Analyze from "./pages/Analyze";
import Docs from "./pages/Docs";
import Dynamic from "./pages/Dynamic";
import History from "./pages/History";
import Mitre from "./pages/Mitre";
import Rules from "./pages/Rules";
import Stats from "./pages/Stats";
import Status from "./pages/Status";

export default function App() {
  const location = useLocation();
  return (
    <Layout>
      <AnimatePresence mode="wait">
        <Routes location={location} key={location.pathname}>
          <Route path="/" element={<Analyze />} />
          <Route path="/dynamic" element={<Dynamic />} />
          <Route path="/mitre" element={<Mitre />} />
          <Route path="/history" element={<History />} />
          <Route path="/rules" element={<Rules />} />
          <Route path="/stats" element={<Stats />} />
          <Route path="/status" element={<Status />} />
          <Route path="/docs" element={<Docs />} />
          <Route path="*" element={<Analyze />} />
        </Routes>
      </AnimatePresence>
    </Layout>
  );
}
