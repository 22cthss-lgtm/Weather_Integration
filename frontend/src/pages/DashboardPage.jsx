import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { fetchLatestImage } from "../api";

const categories = [
  { key: "satellite", label: "Satellite" },
  { key: "radar", label: "Radar" },
  { key: "850hpa", label: "KMA 850hPa" },
  { key: "temperature", label: "Temperature" },
  { key: "rainfall", label: "Rainfall" },
  { key: "weather_chart", label: "CWA Surface Chart" },
  { key: "tchp", label: "CWA TCHP" },
  { key: "cimss_wind_analysis", label: "CIMSS / Wind Analysis" },
  { key: "cimss_steering_flow", label: "CIMSS / Steering Flow" },
  { key: "seaice", label: "NSIDC Sea Ice Extent" },
  { key: "seaice_antarctic", label: "NSIDC Antarctic Sea Ice Extent" },
  { key: "sst", label: "SST" },
];

const categoryMap = Object.fromEntries(categories.map((category) => [category.key, category]));

const sections = [
  {
    title: "Taiwan Real-Time Weather Overview",
    categoryKeys: ["satellite", "radar", "temperature", "rainfall"],
  },
  {
    title: "Synoptic Weather Analysis",
    categoryKeys: ["weather_chart", "850hpa"],
  },
  {
    title: "Ocean and Typhoon Potential",
    categoryKeys: ["tchp", "sst", "cimss_wind_analysis", "cimss_steering_flow"],
  },
  {
    title: "Polar and Climate Monitoring",
    categoryKeys: ["seaice", "seaice_antarctic"],
  },
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
    <section className="dashboard-page">
      <h2>Dashboard</h2>
      <div className="dashboard-sections">
        {sections.map((section) => (
          <section className="dashboard-section" key={section.title}>
            <h3 className="dashboard-section-title">{section.title}</h3>
            <div className="grid">
              {section.categoryKeys.map((categoryKey) => {
                const category = categoryMap[categoryKey];
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
        ))}
      </div>
    </section>
  );
}
