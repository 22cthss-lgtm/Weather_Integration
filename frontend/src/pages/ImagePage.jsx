import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import { fetchLatestImage } from "../api";

const SEA_ICE_TABS = [
  { id: "extent", label: "Sea Ice Extent" },
  { id: "concentration", label: "Sea Ice Concentration" },
  { id: "timeseries", label: "Time Series" },
];

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
  if (isSeaIceCollection(type)) {
    return SEA_ICE_TABS;
  }

  if (type === "cimss_wind_analysis") {
    return CIMSS_WIND_ANALYSIS_TABS;
  }

  if (type === "cimss_steering_flow") {
    return CIMSS_STEERING_FLOW_TABS;
  }

  return null;
}

function isSeaIceCollection(type) {
  return type === "seaice_arctic" || type === "seaice_antarctic";
}

function getCollectionHeading(type) {
  if (type === "seaice_arctic") {
    return "NSIDC Arctic Sea Ice";
  }

  if (type === "seaice_antarctic") {
    return "NSIDC Antarctic Sea Ice";
  }

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

function getSeaIceEntry(images, activeTabId) {
  return images.find((entry) => entry.image_type?.endsWith(`_${activeTabId}`)) || images[0];
}

function getTabbedEntry(type, images, activeTabId) {
  if (isSeaIceCollection(type)) {
    return getSeaIceEntry(images, activeTabId);
  }

  return images.find((entry) => entry.image_type === activeTabId) || images[0];
}

export default function ImagePage() {
  const { type } = useParams();
  const [image, setImage] = useState(null);
  const [error, setError] = useState("");
  const [activeImageTab, setActiveImageTab] = useState(SEA_ICE_TABS[0].id);

  useEffect(() => {
    async function load() {
      try {
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

  if (error) {
    return <p>{error}</p>;
  }

  if (!image) {
    return <p>Loading...</p>;
  }

  if (
    (isSeaIceCollection(type) ||
      type === "cimss_wind_analysis" ||
      type === "cimss_steering_flow") &&
    Array.isArray(image.images)
  ) {
    const tabs = getTabsForType(type);

    if (tabs) {
      const activeEntry = getTabbedEntry(type, image.images, activeImageTab || tabs[0].id);
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
