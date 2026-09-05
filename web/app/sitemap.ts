import type { MetadataRoute } from "next";

export default function sitemap(): MetadataRoute.Sitemap {
  const base = "https://rag.noblechicken.me";
  return ["", "/ask", "/ingest", "/eval", "/system", "/topology"].map(
    (p) => ({
      url: base + p,
      lastModified: new Date(),
    }),
  );
}
