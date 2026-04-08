import { useEffect, useState } from "react";
import ReactMarkdown from "react-markdown";
import { fetchDoc, fetchDocs } from "../api";

export default function DocsPage() {
  const [docs, setDocs] = useState([]);
  const [selectedId, setSelectedId] = useState(null);
  const [selectedDoc, setSelectedDoc] = useState(null);
  const [error, setError] = useState("");

  useEffect(() => {
    async function loadDocs() {
      try {
        const result = await fetchDocs();
        setDocs(result);
        if (result.length > 0) {
          setSelectedId(result[0].id);
        }
      } catch (err) {
        setError(err.message);
      }
    }

    loadDocs();
  }, []);

  useEffect(() => {
    if (!selectedId) {
      return;
    }

    async function loadDoc() {
      try {
        const result = await fetchDoc(selectedId);
        setSelectedDoc(result);
      } catch (err) {
        setError(err.message);
      }
    }

    loadDoc();
  }, [selectedId]);

  if (error) {
    return <p>{error}</p>;
  }

  return (
    <section className="docs-layout">
      <div>
        <h2>Docs</h2>
        <ul>
          {docs.map((doc) => (
            <li key={doc.id}>
              <button type="button" onClick={() => setSelectedId(doc.id)}>
                {doc.title}
              </button>
            </li>
          ))}
        </ul>
      </div>
      <article>
        {selectedDoc ? (
          <>
            <h3>{selectedDoc.title}</h3>
            <ReactMarkdown>{selectedDoc.content}</ReactMarkdown>
          </>
        ) : (
          <p>No document selected.</p>
        )}
      </article>
    </section>
  );
}
