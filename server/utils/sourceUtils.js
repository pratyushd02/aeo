// utils/sourceUtils.js

/**
 * Extract unique domains from text containing URLs
 */
function extractAllDomains(text) {
  if (!text || typeof text !== "string") return [];

  const urls = text.match(/https?:\/\/[^\s)]+/g) || [];

  const domains = urls.map((url) => {
    try {
      const hostname = new URL(url).hostname.replace("www.", "");
      return hostname.toLowerCase();
    } catch {
      return null;
    }
  }).filter(Boolean);

  return [...new Set(domains)];
}

/**
 * Classify source domain into category
 */
function classifySource(domain) {
  const d = domain.toLowerCase();

  if (
    ["facebook", "linkedin", "twitter", "instagram", "youtube", "tiktok", "reddit"]
      .some((x) => d.includes(x))
  ) {
    return "Social Media";
  }

  if (d.includes(".edu")) return "University Website";
  if (d.includes(".gov") || d.includes(".ac")) return "Government/Educational Body";

  if (
    [".com", ".org", ".net", "news", "college", "ranking", "review"]
      .some((x) => d.includes(x))
  ) {
    return "News / Articles / Blogs";
  }

  return "Miscellaneous";
}

module.exports = {
  extractAllDomains,
  classifySource,
};