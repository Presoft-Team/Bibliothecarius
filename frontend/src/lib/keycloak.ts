import Keycloak from "keycloak-js";

export const keycloak = new Keycloak({
  url: import.meta.env.VITE_KEYCLOAK_URL ?? "http://localhost:8081",
  realm: import.meta.env.VITE_KEYCLOAK_REALM ?? "ragchat",
  clientId: import.meta.env.VITE_KEYCLOAK_CLIENT_ID ?? "ragchat-frontend",
});

let initPromise: Promise<boolean> | null = null;

export function initKeycloak(): Promise<boolean> {
  if (!initPromise) {
    initPromise = keycloak.init({
      onLoad: "login-required",
      pkceMethod: "S256",
    });
  }
  return initPromise;
}
