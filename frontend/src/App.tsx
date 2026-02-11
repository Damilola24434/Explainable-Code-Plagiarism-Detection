import { useEffect, useState } from "react";

export default function App() {
  const [status, setStatus] = useState("loading...");

  useEffect(() => {
    fetch("/api/health")
      .then((r) => r.json())
      .then((d) => setStatus(d.status))
      .catch(() => setStatus("error"));
  }, []);

  return <div style={{ padding: 24, fontSize: 24 }}>Backend: {status}</div>;
}
