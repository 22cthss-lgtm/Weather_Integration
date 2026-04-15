import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { fetchLatestImage } from "../api";

const categories = [
  { key: "satellite", label: "Satellite" },
  { key: "radar", label: "Radar" },
  { key: "850hpa", label: "KMA 850hPa" },
  { key: "temperature", label: "Temperature" },
  { key: "rainfall", label: "累積雨量" },
  { key: "aqi", label: "AQI" },
  { key: "sst", label: "SST" },
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
              {card ? (
                <p className="card-meta">
                  {card.image_time ? `Image Time: ${card.image_time}` : `Fetched At: ${card.fetched_at}`}
                </p>
              ) : null}
              <Link to={`/images/${category.key}`}>View latest</Link>
            </article>
          );
        })}
      </div>
    </section>
  );
}
