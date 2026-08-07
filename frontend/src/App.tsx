import { NavLink, Route, Routes } from "react-router-dom";
import { MessageSquare, FolderOpen, Sparkles, SlidersHorizontal, Users, LogOut, BookOpen } from "lucide-react";
import ChatPage from "./pages/ChatPage";
import DocumentsPage from "./pages/DocumentsPage";
import TonesPage from "./pages/TonesPage";
import AssistantSettingsPage from "./pages/AssistantSettingsPage";
import UsersPage from "./pages/UsersPage";
import { keycloak } from "./lib/keycloak";
import { AuthProvider, useAuth } from "./lib/AuthContext";

const NAV_ITEMS = [
  { to: "/", label: "Chat", icon: MessageSquare },
  { to: "/documents", label: "Documents", icon: FolderOpen },
  { to: "/tones", label: "Tones", icon: Sparkles },
  { to: "/settings", label: "Assistant Settings", icon: SlidersHorizontal },
];

function AppShell() {
  const { currentUser } = useAuth();
  const username = keycloak.tokenParsed?.preferred_username as string | undefined;

  return (
    <div className="flex min-h-screen">
      <nav className="flex w-60 shrink-0 flex-col border-r border-slate-200 bg-white p-4 dark:border-slate-800 dark:bg-slate-900">
        <div className="mb-6 flex items-center gap-2 px-2">
          <BookOpen className="h-6 w-6 text-accent-600 dark:text-accent-400" />
          <span className="text-lg font-semibold text-slate-900 dark:text-white">Bibliothecarius</span>
        </div>

        <div className="flex flex-1 flex-col gap-1">
          {NAV_ITEMS.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              end={item.to === "/"}
              className={({ isActive }) =>
                `flex items-center gap-2.5 rounded-lg px-3 py-2 text-sm font-medium transition-colors ${
                  isActive
                    ? "bg-accent-50 text-accent-700 dark:bg-accent-900/40 dark:text-accent-300"
                    : "text-slate-600 hover:bg-slate-100 dark:text-slate-300 dark:hover:bg-slate-800"
                }`
              }
            >
              <item.icon className="h-4 w-4" />
              {item.label}
            </NavLink>
          ))}
          {currentUser?.role === "admin" && (
            <NavLink
              to="/users"
              className={({ isActive }) =>
                `flex items-center gap-2.5 rounded-lg px-3 py-2 text-sm font-medium transition-colors ${
                  isActive
                    ? "bg-accent-50 text-accent-700 dark:bg-accent-900/40 dark:text-accent-300"
                    : "text-slate-600 hover:bg-slate-100 dark:text-slate-300 dark:hover:bg-slate-800"
                }`
              }
            >
              <Users className="h-4 w-4" />
              Users
            </NavLink>
          )}
        </div>

        <div className="flex items-center justify-between gap-2 border-t border-slate-200 pt-3 dark:border-slate-800">
          <span className="min-w-0 truncate text-sm text-slate-600 dark:text-slate-400">{username}</span>
          <button
            type="button"
            title="Log out"
            onClick={() => keycloak.logout()}
            className="rounded-lg p-1.5 text-slate-500 hover:bg-slate-100 hover:text-slate-700 dark:text-slate-400 dark:hover:bg-slate-800 dark:hover:text-slate-200"
          >
            <LogOut className="h-4 w-4" />
          </button>
        </div>
      </nav>

      <main className="min-w-0 flex-1 overflow-x-auto p-6 md:p-8">
        <Routes>
          <Route path="/" element={<ChatPage />} />
          <Route path="/documents" element={<DocumentsPage />} />
          <Route path="/tones" element={<TonesPage />} />
          <Route path="/settings" element={<AssistantSettingsPage />} />
          <Route path="/users" element={<UsersPage />} />
        </Routes>
      </main>
    </div>
  );
}

function App() {
  return (
    <AuthProvider>
      <AppShell />
    </AuthProvider>
  );
}

export default App;
