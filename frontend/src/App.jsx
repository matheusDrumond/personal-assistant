import { useState } from "react";
import "./App.css";
import { typeColors, typeLabels } from "./constants";

const App = () => {
    const [message, setMessage] = useState("");
    const [result, setResult] = useState(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);

    const handleSubmit = async () => {
        if (!message.trim()) return;
        setLoading(true);
        setError(null);
        setResult(null);

        try {
            const response = await fetch("http://localhost:8000/process", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ message }),
            });

            if (!response.ok) throw new Error("Error processing message");
            const data = await response.json();
            setResult(data);
        } catch (err) {
            setError(err.message);
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="container">
            <header>
                <h1>Personal Assistant</h1>
                <p>Type anything — I'll organize it in Notion.</p>
            </header>

            <div className="input-area">
                <textarea
                    value={message}
                    onChange={(e) => setMessage(e.target.value)}
                    placeholder="e.g. call the client tomorrow at 10am..."
                    rows={4}
                    onKeyDown={(e) => {
                        if (e.key === "Enter" && e.metaKey) handleSubmit();
                    }}
                />
                <button onClick={handleSubmit} disabled={loading}>
                    {loading ? "Processing..." : "Send"}
                </button>
            </div>

            {error && <div className="error">{error}</div>}

            {result && (
                <div className="result">
                    <div
                        className="type-badge"
                        style={{ background: typeColors[result.type] }}
                    >
                        {typeLabels[result.type]}
                    </div>
                    <h2>{result.title}</h2>
                    <div className="meta">
                        <span>Priority: {result.priority}</span>
                    </div>
                    <a
                        href={result.notion_url}
                        target="_blank"
                        rel="noreferrer"
                    >
                        View in Notion →
                    </a>
                </div>
            )}
        </div>
    );
};

export default App;
