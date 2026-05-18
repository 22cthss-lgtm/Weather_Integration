import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import { backfillImages, fetchDailyImages, fetchImageHistory, fetchLatestImage } from "../api";

const CIMSS_WIND_ANALYSIS_TABS = [
  { id: "cimss_wind_shear", label: "Wind Shear" },
  { id: "cimss_850mb_vorticity", label: "850mb Vorticity" },
];

const CIMSS_STEERING_FLOW_TABS = [
  { id: "cimss_steering_flow_200_700mb", label: "200 - 700 mb" },
  { id: "cimss_steering_flow_250_850mb", label: "250 - 850 mb" },
  { id: "cimss_steering_flow_300_850mb", label: "300 - 850 mb" },
  { id: "cimss_steering_flow_400_850mb", label: "400 - 850 mb" },
  { id: "cimss_steering_flow_500_850mb", label: "500 - 850 mb" },
  { id: "cimss_steering_flow_700_850mb", label: "700 - 850 mb" },
];

function getTabsForType(type) {
  if (type === "cimss_wind_analysis") {
    return CIMSS_WIND_ANALYSIS_TABS;
  }

  if (type === "cimss_steering_flow") {
    return CIMSS_STEERING_FLOW_TABS;
  }

  return null;
}

function getCollectionHeading(type) {
  if (type === "cimss_wind_analysis") {
    return "CIMSS Wind Analysis";
  }

  if (type === "cimss_steering_flow") {
    return "CIMSS Steering Flow";
  }

  return "";
}

function getDisplayTitle(type, entry) {
  return entry.title;
}

function getImageDate(entry) {
  return entry?.image_time?.slice(0, 10) || "";
}

function formatBackfillSummary(summary) {
  if (!summary) {
    return "";
  }

  return `Backfill complete: ${summary.inserted} inserted, ${summary.skipped_existing} already existed, ${summary.missing} missing, ${summary.failed} failed.`;
}

function getTabbedEntry(images, activeTabId) {
  return images.find((entry) => entry.image_type === activeTabId) || images[0];
}

export default function ImagePage() {
  const { type } = useParams();
  const [image, setImage] = useState(null);
  const [error, setError] = useState("");
  const [activeImageTab, setActiveImageTab] = useState("");
  const [rainfallHistory, setRainfallHistory] = useState([]);
  const [selectedRainfallTime, setSelectedRainfallTime] = useState("");
  const [rainfallDailyImages, setRainfallDailyImages] = useState([]);
  const [isBackfilling, setIsBackfilling] = useState(false);
  const [backfillSummary, setBackfillSummary] = useState(null);

  async function loadRainfallData() {
    const latest = await fetchLatestImage("rainfall");
    const historyDate = getImageDate(latest);
    const [history, dailyImages] = historyDate
      ? await Promise.all([
          fetchImageHistory("rainfall", { date: historyDate }),
          fetchDailyImages("rainfall", { date: historyDate }),
        ])
      : [[], []];
    const selectableHistory = history.filter((entry) => !entry.image_time?.endsWith("00:00"));
    const hasLatestInHistory = selectableHistory.some((entry) => entry.image_time === latest.image_time);

    setImage(latest);
    setRainfallHistory(selectableHistory);
    setRainfallDailyImages(dailyImages);
    setSelectedRainfallTime(hasLatestInHistory ? latest.image_time : selectableHistory.at(-1)?.image_time || latest.image_time || "");
  }

  useEffect(() => {
    async function load() {
      try {
        setError("");
        setImage(null);
        setBackfillSummary(null);
        setRainfallHistory([]);
        setRainfallDailyImages([]);
        setSelectedRainfallTime("");

        if (type === "rainfall") {
          await loadRainfallData();
          return;
        }

        const result = await fetchLatestImage(type);
        setImage(result);
      } catch (err) {
        setError(err.message);
      }
    }

    load();
  }, [type]);

  useEffect(() => {
    const tabs = getTabsForType(type);
    setActiveImageTab(tabs?.[0].id || "");
  }, [type]);

  async function handleBackfillRainfall() {
    setIsBackfilling(true);
    setError("");

    try {
      const summary = await backfillImages("rainfall", { range: "today" });
      setBackfillSummary(summary);
      await loadRainfallData();
    } catch (err) {
      setError(err.message);
    } finally {
      setIsBackfilling(false);
    }
  }

  if (error) {
    return <p>{error}</p>;
  }

  if (!image) {
    return <p>Loading...</p>;
  }

  if (type === "rainfall") {
    const selectedRainfall =
      rainfallHistory.find((entry) => entry.image_time === selectedRainfallTime) || image;
    const backfillMessage = formatBackfillSummary(backfillSummary);

    return (
      <section>
        <h2>{selectedRainfall.title}</h2>
        <div className="image-meta-row">
          <p>Source: {selectedRainfall.source}</p>
          <p>{selectedRainfall.image_time ? `Image Time: ${selectedRainfall.image_time}` : `Fetched At: ${selectedRainfall.fetched_at}`}</p>
        </div>
        <div className="rainfall-detail-layout">
          <div className="rainfall-controls">
            <label className="rainfall-time-select">
              <span>Today Available Rainfall Images</span>
              <select
                value={selectedRainfallTime}
                onChange={(event) => setSelectedRainfallTime(event.target.value)}
                disabled={!rainfallHistory.length}
              >
                {rainfallHistory.map((entry) => (
                  <option value={entry.image_time} key={`${entry.id}-${entry.image_time}`}>
                    {entry.image_time}
                  </option>
                ))}
              </select>
            </label>
            <button
              className="primary-button rainfall-backfill-button"
              type="button"
              onClick={handleBackfillRainfall}
              disabled={isBackfilling}
            >
              {isBackfilling ? "Backfilling..." : "Backfill Images"}
            </button>
            <p className="status-message rainfall-status" aria-live="polite">
              {backfillMessage || (rainfallHistory.length ? `${rainfallHistory.length} images available for this date.` : "No rainfall history loaded.")}
            </p>
            <p className="rainfall-source-link">
              <a href={selectedRainfall.source_url} target="_blank" rel="noreferrer">
                Original source
              </a>
            </p>
          </div>
          <img className="detail-image rainfall-detail-image" src={selectedRainfall.image_url} alt={selectedRainfall.title} />
          {rainfallDailyImages.length ? (
            <section className="rainfall-daily-section" aria-label="Daily rainfall representatives">
              <div className="rainfall-daily-grid">
                {rainfallDailyImages.map((entry) => (
                  <article className="image-panel rainfall-daily-card" key={`${entry.label}-${entry.image_time}`}>
                    <p>{entry.represented_date}</p>
                    <img className="detail-image rainfall-daily-image" src={entry.image_url} alt={`${entry.label} ${entry.represented_date}`} />
                  </article>
                ))}
              </div>
            </section>
          ) : null}
        </div>
      </section>
    );
  }

  if (
    (type === "cimss_wind_analysis" || type === "cimss_steering_flow") &&
    Array.isArray(image.images)
  ) {
    const tabs = getTabsForType(type);

    if (tabs) {
      const activeEntry = getTabbedEntry(image.images, activeImageTab || tabs[0].id);
      const activeTitle = getDisplayTitle(type, activeEntry);
      const tabPanelId = `${type}-tab-panel`;

      return (
        <section>
          <h2>{getCollectionHeading(type)}</h2>
          <div className="image-meta-row">
            <p>Source: {image.source}</p>
            <p>{activeEntry.image_time ? `Image Time: ${activeEntry.image_time}` : `Fetched At: ${activeEntry.fetched_at}`}</p>
          </div>
          <div className="image-tabs" role="tablist" aria-label={`${getCollectionHeading(type)} views`}>
            {tabs.map((tab) => {
              const isActive = activeImageTab === tab.id;

              return (
                <button
                  className={isActive ? "image-tab active" : "image-tab"}
                  type="button"
                  role="tab"
                  aria-selected={isActive}
                  aria-controls={tabPanelId}
                  id={`${type}-tab-${tab.id}`}
                  key={tab.id}
                  onClick={() => setActiveImageTab(tab.id)}
                >
                  {tab.label}
                </button>
              );
            })}
          </div>
          <article
            className="image-panel image-tab-panel"
            role="tabpanel"
            id={tabPanelId}
            aria-labelledby={`${type}-tab-${activeImageTab}`}
          >
            <img className="detail-image" src={activeEntry.image_url} alt={activeTitle} />
          </article>
          <p>
            <a href={image.source_url} target="_blank" rel="noreferrer">
              Original source
            </a>
          </p>
        </section>
      );
    }

    return (
      <section>
        <h2>{getCollectionHeading(type)}</h2>
        <p>Source: {image.source}</p>
        <div className="image-collection">
          {image.images.map((entry) => (
            <article className="image-panel" key={entry.image_type}>
              <h3>{getDisplayTitle(type, entry)}</h3>
              <p>{entry.image_time ? `Image Time: ${entry.image_time}` : `Fetched At: ${entry.fetched_at}`}</p>
              <img className="detail-image" src={entry.image_url} alt={getDisplayTitle(type, entry)} />
            </article>
          ))}
        </div>
        <p>
          <a href={image.source_url} target="_blank" rel="noreferrer">
            Original source
          </a>
        </p>
      </section>
    );
  }

  return (
    <section>
      <h2>{image.title}</h2>
      <p>Source: {image.source}</p>
      <p>{image.image_time ? `Image Time: ${image.image_time}` : `Fetched At: ${image.fetched_at}`}</p>
      <img className="detail-image" src={image.image_url} alt={image.title} />
      <p>
        <a href={image.source_url} target="_blank" rel="noreferrer">
          Original source
        </a>
      </p>
    </section>
  );
}
