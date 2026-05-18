import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import { fetchLatestImage } from "../api";

const compactImageTypes = new Set(["temperature", "radar", "satellite", "weather_chart", "850hpa", "tchp", "sst"]);

export default function ImagePage() {
  const { type } = useParams();
  const [image, setImage] = useState(null);
  const [error, setError] = useState("");
  const sectionClassNames = ["image-detail-page"];

  if (compactImageTypes.has(type)) {
    sectionClassNames.push("image-detail-page-compact");
  }

  if (type === "tchp") {
    sectionClassNames.push("image-detail-page-tchp");
  }

  const sectionClassName = sectionClassNames.join(" ");

  useEffect(() => {
    async function load() {
      try {
        setError("");
        setImage(null);

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

  return (
    <section className={sectionClassName}>
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
