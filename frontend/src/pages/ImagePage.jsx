import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import { fetchLatestImage } from "../api";

export default function ImagePage() {
  const { type } = useParams();
  const [image, setImage] = useState(null);
  const [error, setError] = useState("");

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

  if (error) {
    return <p>{error}</p>;
  }

  if (!image) {
    return <p>Loading...</p>;
  }

  if ((type === "seaice" || type === "seaice_antarctic") && Array.isArray(image.images)) {
    const heading = type === "seaice_antarctic" ? "NSIDC Antarctic Sea Ice" : "NSIDC Sea Ice";
    return (
      <section>
        <h2>{heading}</h2>
        <p>Source: {image.source}</p>
        <div className="image-collection">
          {image.images.map((entry) => (
            <article className="image-panel" key={entry.image_type}>
              <h3>{entry.title}</h3>
              <p>{entry.image_time ? `Image Time: ${entry.image_time}` : `Fetched At: ${entry.fetched_at}`}</p>
              <img className="detail-image" src={entry.image_url} alt={entry.title} />
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
