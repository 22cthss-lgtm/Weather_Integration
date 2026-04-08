import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { fetchLatestImage } from "../api";

const categories = [
  { key: "satellite", label: "Satellite" },
  { key: "radar", label: "Radar" },
  { key: "aqi", label: "AQI" },
  { key: "ohc", label: "OHC" },
  { key: "reservoir", label: "Reservoir" },
];

export default function DashboardPage() {
  const [cards, setCards] = useState({});

  useEffect(() => {
    async function load() {
      const results = await Promise.allSettled(
        categories.map(async (category) => [category.key, await fetchLatestImage(category.key)])
      );

      const successfulCards = results
        .filter((result) => result.status === "fulfilled")
        .map((result) => result.value);

      setCards(Object.fromEntries(successfulCards));
    }

    load();
  }, []);

  return (
    <section>
      <h2>Dashboard</h2>
      <div className="grid">
        {categories.map((category) => {
          const card = cards[category.key];
          return (
            <article className="card" key={category.key}>
              <h3>{category.label}</h3>
              {card ? <img src={card.image_url} alt={card.title} /> : <p>Loading...</p>}
              <Link to={`/images/${category.key}`}>View latest</Link>
            </article>
          );
        })}
      </div>
    </section>
  );
}
