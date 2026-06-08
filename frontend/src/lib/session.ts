export type ConnectionStatus = "connected" | "incomplete_scopes" | "reconnect_required" | "disconnected";

export type MeResponse = {
  authenticated: boolean;
  user: {
    id: string;
    email: string | null;
    email_verified: boolean;
    name: string | null;
    avatar_url: string | null;
  } | null;
  youtube: {
    connection_status: ConnectionStatus;
    granted_scopes: string[];
    missing_scopes: string[];
    reconnect_needed: boolean;
    last_verified_at: string | null;
  };
  csrf_token: string | null;
};

export async function fetchCurrentSession() {
  const response = await fetch("/api/me", {
    cache: "no-store",
    credentials: "include"
  });

  if (!response.ok) {
    throw new Error("Connection status is unavailable.");
  }

  return (await response.json()) as MeResponse;
}

export function hasCompleteYouTubeAccess(me: MeResponse | null) {
  return Boolean(
    me?.authenticated &&
      me.youtube.connection_status === "connected" &&
      !me.youtube.reconnect_needed &&
      me.youtube.missing_scopes.length === 0
  );
}

export function connectionLabel(status: ConnectionStatus) {
  if (status === "connected") return "Connected";
  if (status === "incomplete_scopes") return "Access incomplete";
  if (status === "reconnect_required") return "Reconnect needed";
  return "Not connected";
}

export function formatSessionDate(value: string | null) {
  if (!value) return null;

  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return null;

  return {
    dateTime: value,
    label: new Intl.DateTimeFormat(undefined, {
      day: "numeric",
      hour: "numeric",
      minute: "2-digit",
      month: "short"
    }).format(date)
  };
}
