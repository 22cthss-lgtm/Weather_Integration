import { useEffect, useMemo, useState } from "react";
import { fetchImageStatus, refreshImage } from "../api";

const STATUS_SORT_ORDER = {
  Fresh: 0,
  Stale: 1,
  Unknown: 2,
  "No Data": 3,
};
const REFRESHABLE_IMAGE_TYPES = new Set(["radar", "satellite", "temperature", "rainfall"]);

const STATUS_CLASS_BY_VALUE = {
  Fresh: "status-badge-fresh",
  Stale: "status-badge-stale",
  "No Data": "status-badge-empty",
  Unknown: "status-badge-unknown",
};

function displayValue(value) {
  if (value === null || value === undefined || value === "") {
    return "N/A";
  }

  if (typeof value === "boolean") {
    return value ? "Yes" : "No";
  }

  return String(value);
}

function formatDateTime(value) {
  if (!value) {
    return "N/A";
  }

  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) {
    return "N/A";
  }

  return parsed.toLocaleString("zh-TW", {
    timeZone: "Asia/Taipei",
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
  });
}

function statusBadgeClass(status) {
  return `status-badge ${STATUS_CLASS_BY_VALUE[status] || "status-badge-unknown"}`;
}

export default function StatusPage() {
  const [payload, setPayload] = useState(null);
  const [error, setError] = useState("");
  const [isLoading, setIsLoading] = useState(true);
  const [statusSortDirection, setStatusSortDirection] = useState("asc");
  const [refreshingType, setRefreshingType] = useState("");
  const [refreshMessage, setRefreshMessage] = useState("");

  async function loadStatus({ showLoading = true } = {}) {
    try {
      if (showLoading) {
        setIsLoading(true);
      }
      setError("");

      const result = await fetchImageStatus();
      setPayload(result);
    } catch (err) {
      setError(err.message);
    } finally {
      if (showLoading) {
        setIsLoading(false);
      }
    }
  }

  useEffect(() => {
    let isMounted = true;

    async function loadInitialStatus() {
      if (!isMounted) {
        return;
      }
      await loadStatus();
    }

    loadInitialStatus();

    return () => {
      isMounted = false;
    };
  }, []);

  const items = Array.isArray(payload?.items) ? payload.items : [];
  const sortedItems = useMemo(() => {
    return [...items].sort((first, second) => {
      const firstRank = STATUS_SORT_ORDER[first.freshness_status] ?? 99;
      const secondRank = STATUS_SORT_ORDER[second.freshness_status] ?? 99;
      const rankDelta = firstRank - secondRank;

      if (rankDelta !== 0) {
        return statusSortDirection === "asc" ? rankDelta : -rankDelta;
      }

      return displayValue(first.image_type).localeCompare(displayValue(second.image_type));
    });
  }, [items, statusSortDirection]);

  function toggleStatusSortDirection() {
    setStatusSortDirection((current) => (current === "asc" ? "desc" : "asc"));
  }

  async function handleRefresh(imageType) {
    try {
      setRefreshingType(imageType);
      setRefreshMessage("");
      setError("");

      await refreshImage(imageType);
      await loadStatus({ showLoading: false });
      setRefreshMessage(`${imageType} refreshed.`);
    } catch (err) {
      setError(err.message);
    } finally {
      setRefreshingType("");
    }
  }

  return (
    <section className="status-page">
      <header className="status-page-header">
        <div>
          <h2>Weather Integration Status</h2>
          <p>Read-only DB summary for current image metadata. Opening this page does not refresh external sources.</p>
          <p>Generated: {formatDateTime(payload?.generated_at)}</p>
        </div>
      </header>

      {isLoading ? <p className="status-message">Loading status data...</p> : null}
      {refreshMessage ? <p className="status-message">{refreshMessage}</p> : null}
      {error ? <p className="error-message">Unable to load status data: {error}</p> : null}
      {!isLoading && !error && items.length === 0 ? (
        <div className="status-empty-state">
          <h3>No status data</h3>
          <p>The status API returned no image status rows.</p>
        </div>
      ) : null}

      {!isLoading && !error && items.length > 0 ? (
        <div className="status-table-panel">
          <div className="status-table-wrap">
            <table className="status-table">
              <thead>
                <tr>
                  <th>Image Type</th>
                  <th className="status-table-th-narrow">Source</th>
                  <th className="status-table-th-narrow">
                    <button
                      className="status-sort-button"
                      type="button"
                      onClick={toggleStatusSortDirection}
                      aria-label="Sort status column"
                    >
                      Status {statusSortDirection === "asc" ? "↑" : "↓"}
                    </button>
                  </th>
                  <th className="status-table-th-narrow">Total</th>
                  <th className="status-table-th-narrow">Today</th>
                  <th className="status-table-th-narrow">Last 24h</th>
                  <th>Latest Fetched</th>
                  <th>Data Time</th>
                  <th className="status-table-th-narrow">Same URL</th>
                  <th className="status-table-th-narrow">Duplicates</th>
                  <th>Latest Title</th>
                  <th>Latest URL</th>
                  <th>Previous URL</th>
                  <th>Note</th>
                  <th>Action</th>
                </tr>
              </thead>
              <tbody>
                {sortedItems.map((item) => (
                  <tr key={item.image_type}>
                    <td className="status-type-cell">{displayValue(item.image_type)}</td>
                    <td>{displayValue(item.source)}</td>
                    <td>
                      <span className={statusBadgeClass(item.freshness_status)}>
                        {displayValue(item.freshness_status)}
                      </span>
                    </td>
                    <td>{displayValue(item.total_records)}</td>
                    <td>{displayValue(item.added_today)}</td>
                    <td>{displayValue(item.added_last_24h)}</td>
                    <td>{formatDateTime(item.latest_fetched_at)}</td>
                    <td>{displayValue(item.latest_data_time)}</td>
                    <td>{displayValue(item.latest_url_same_as_previous)}</td>
                    <td>{displayValue(item.possible_duplicate_count)}</td>
                    <td className="status-long-cell">{displayValue(item.latest_title)}</td>
                    <td className="status-url-cell">{displayValue(item.latest_image_url)}</td>
                    <td className="status-url-cell">{displayValue(item.previous_image_url)}</td>
                    <td className="status-note-cell">{displayValue(item.note)}</td>
                    <td>
                      {REFRESHABLE_IMAGE_TYPES.has(item.image_type) ? (
                        <button
                          className="status-refresh-button"
                          type="button"
                          onClick={() => handleRefresh(item.image_type)}
                          disabled={refreshingType === item.image_type}
                        >
                          {refreshingType === item.image_type ? "Refreshing..." : "Refresh"}
                        </button>
                      ) : (
                        <span className="status-action-empty">N/A</span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      ) : null}
    </section>
  );
}
