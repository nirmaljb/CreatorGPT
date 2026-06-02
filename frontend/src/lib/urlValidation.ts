export type Platform = "youtube" | "instagram";

export type VideoInputForValidation = {
  video_id: "A" | "B";
  platform: Platform;
  url: string;
};

export type VideoValidation = {
  normalizedUrl: string;
  error: string | null;
};

function parseHttpUrl(rawUrl: string): URL | null {
  const trimmed = rawUrl.trim();
  if (!trimmed) return null;
  try {
    const url = new URL(trimmed);
    if (url.protocol !== "http:" && url.protocol !== "https:") return null;
    return url;
  } catch {
    return null;
  }
}

function hostMatches(hostname: string, root: string) {
  const host = hostname.toLowerCase();
  return host === root || host.endsWith(`.${root}`);
}

function hasPathToken(pathname: string, index = 0) {
  const parts = pathname.split("/").filter(Boolean);
  return parts.length > index && Boolean(parts[index]?.trim());
}

export function isValidYouTubeUrl(rawUrl: string) {
  const url = parseHttpUrl(rawUrl);
  if (!url) return false;

  const host = url.hostname.toLowerCase();
  if (host === "youtu.be") return hasPathToken(url.pathname);
  if (!hostMatches(host, "youtube.com")) return false;

  if (url.pathname.replace(/\/+$/, "").toLowerCase() === "/watch") {
    return Boolean(url.searchParams.get("v")?.trim());
  }

  const parts = url.pathname.split("/").filter(Boolean);
  return parts.length >= 2 && parts[0]?.toLowerCase() === "shorts" && Boolean(parts[1]?.trim());
}

export function isValidInstagramReelUrl(rawUrl: string) {
  const url = parseHttpUrl(rawUrl);
  if (!url || !hostMatches(url.hostname, "instagram.com")) return false;

  const parts = url.pathname.split("/").filter(Boolean);
  return parts.length >= 2 && parts[0]?.toLowerCase() === "reel" && Boolean(parts[1]?.trim());
}

export function validateVideoUrl(platform: Platform, rawUrl: string): VideoValidation {
  const normalizedUrl = rawUrl.trim();
  if (!normalizedUrl) {
    return { normalizedUrl, error: "Enter a URL for this video." };
  }

  if (platform === "youtube") {
    if (isValidYouTubeUrl(normalizedUrl)) return { normalizedUrl, error: null };
    if (isValidInstagramReelUrl(normalizedUrl)) {
      return { normalizedUrl, error: "Selected platform is YouTube, but the URL is an Instagram Reel." };
    }
    return {
      normalizedUrl,
      error: "Enter a supported YouTube URL: youtube.com/watch, youtube.com/shorts, or youtu.be."
    };
  }

  if (isValidInstagramReelUrl(normalizedUrl)) return { normalizedUrl, error: null };
  if (isValidYouTubeUrl(normalizedUrl)) {
    return { normalizedUrl, error: "Selected platform is Instagram, but the URL is a YouTube video." };
  }
  return { normalizedUrl, error: "Enter a supported Instagram Reel URL in the form instagram.com/reel/..." };
}

export function normalizeVideoInputs(videos: VideoInputForValidation[]) {
  return videos.map((video) => ({
    ...video,
    platform: video.platform,
    url: video.url.trim()
  }));
}

export function duplicateUrlWarning(videos: VideoInputForValidation[]) {
  const [first, second] = videos.map((video) => video.url.trim()).filter(Boolean);
  if (first && second && first === second) {
    return "Video A and Video B use the same URL. Submission is allowed.";
  }
  return null;
}

export function sameInputs(a: VideoInputForValidation[] | null, b: VideoInputForValidation[] | null) {
  if (!a || !b || a.length !== b.length) return false;
  return a.every((video, index) => {
    const other = b[index];
    return (
      other &&
      video.video_id === other.video_id &&
      video.platform === other.platform &&
      video.url.trim() === other.url.trim()
    );
  });
}
