// IndexDB Service for persistent chat history
interface Message {
  id: string;
  role: "user" | "ai";
  text: string;
  timestamp: Date;
  attachments?: { name: string; type: string; preview?: string }[];
  chartData?: any[];
  confidence?: string;
  sampleSize?: number;
  execMs?: number;
  isError?: boolean;
}

interface ChatSession {
  id: string;
  title: string;
  createdAt: Date;
  updatedAt: Date;
  messages: Message[];
}

const DB_NAME = "InsightXDB";
const DB_VERSION = 1;
const SESSIONS_STORE = "chatSessions";
const CURRENT_SESSION_KEY = "currentSessionId";
const DEFAULT_SESSION_TITLE_PREFIX = "Chat - ";
const MAX_SESSION_TITLE_LEN = 72;

const normalizeTitleText = (text: string): string => {
  return text
    .replace(/```[\s\S]*?```/g, " ")
    .replace(/`[^`]*`/g, " ")
    .replace(/\[([^\]]+)\]\([^)]+\)/g, "$1")
    .replace(/^#{1,6}\s+/gm, "")
    .replace(/^\s*[-*+]\s+/gm, "")
    .replace(/^\s*\d+\.\s+/gm, "")
    .replace(/\|/g, " ")
    .replace(/\s+/g, " ")
    .replace(/^[#>*`\-:\s]+/, "")
    .replace(/^(answer|summary|result|insight)\s*:\s*/i, "")
    .trim();
};

const summarizeTitle = (text: string): string => {
  const normalized = normalizeTitleText(text);
  if (!normalized) return "";
  const candidateLines = normalized
    .split(/\r?\n|[;|]/)
    .map((s) => s.trim())
    .filter((s) => s.split(/\s+/).length >= 4);
  const base = candidateLines[0] || normalized;
  const sentences = base
    .split(/(?<=[.!?])\s+/)
    .map((s) => s.trim())
    .filter(Boolean);
  const explanatory = sentences.find((s) => !s.endsWith("?")) || sentences[0] || base;
  const oneLine = explanatory.replace(/\n/g, " ").trim();
  return oneLine.length > MAX_SESSION_TITLE_LEN
    ? `${oneLine.slice(0, MAX_SESSION_TITLE_LEN - 1).trimEnd()}...`
    : oneLine;
};

const deriveSessionTitle = (messages: Message[], existingTitle?: string): string => {
  const persistedTitle = (existingTitle || "").trim();
  if (persistedTitle && !persistedTitle.startsWith(DEFAULT_SESSION_TITLE_PREFIX)) {
    return summarizeTitle(persistedTitle);
  }

  const firstAiMessage = messages.find(
    (msg) => msg.role === "ai" && !msg.isError && msg.text.trim()
  );
  if (firstAiMessage) {
    const aiSummary = summarizeTitle(firstAiMessage.text);
    if (aiSummary) return aiSummary;
  }

  const firstUserMessage = messages.find(
    (msg) => msg.role === "user" && msg.text.trim()
  );
  if (firstUserMessage) {
    const userSummary = summarizeTitle(firstUserMessage.text);
    if (userSummary) return `Discussion: ${userSummary}`.slice(0, MAX_SESSION_TITLE_LEN);
  }

  return persistedTitle || `Chat - ${new Date().toLocaleDateString()}`;
};

export const indexdbService = {
  /**
   * Initialize the IndexDB database
   */
  initDB: async (): Promise<IDBDatabase> => {
    return new Promise((resolve, reject) => {
      const request = indexedDB.open(DB_NAME, DB_VERSION);

      request.onerror = () => reject(request.error);
      request.onsuccess = () => resolve(request.result);

      request.onupgradeneeded = (event) => {
        const db = (event.target as IDBOpenDBRequest).result;

        // Create object store for chat sessions if it doesn't exist
        if (!db.objectStoreNames.contains(SESSIONS_STORE)) {
          const store = db.createObjectStore(SESSIONS_STORE, { keyPath: "id" });
          store.createIndex("createdAt", "createdAt", { unique: false });
          store.createIndex("updatedAt", "updatedAt", { unique: false });
        }
      };
    });
  },

  /**
   * Save a message to the current session
   */
  saveMessage: async (message: Message): Promise<void> => {
    try {
      const db = await indexdbService.initDB();
      const sessionId = await indexdbService.getCurrentSessionId();

      const transaction = db.transaction([SESSIONS_STORE], "readwrite");
      const store = transaction.objectStore(SESSIONS_STORE);

      const getRequest = store.get(sessionId);

      return new Promise((resolve, reject) => {
        getRequest.onsuccess = () => {
          const session = getRequest.result || {
            id: sessionId,
            title: `Chat - ${new Date().toLocaleDateString()}`,
            createdAt: new Date(),
            updatedAt: new Date(),
            messages: [],
          };

          session.messages.push(message);
          session.updatedAt = new Date();
          session.title = deriveSessionTitle(session.messages, session.title);

          const putRequest = store.put(session);
          putRequest.onsuccess = () => resolve();
          putRequest.onerror = () => reject(putRequest.error);
        };
        getRequest.onerror = () => reject(getRequest.error);
      });
    } catch (error) {
      console.error("Failed to save message to IndexDB:", error);
    }
  },

  /**
   * Load all messages from the current session
   */
  loadMessages: async (): Promise<Message[]> => {
    try {
      const db = await indexdbService.initDB();
      const sessionId = await indexdbService.getCurrentSessionId();

      return new Promise((resolve, reject) => {
        const transaction = db.transaction([SESSIONS_STORE], "readonly");
        const store = transaction.objectStore(SESSIONS_STORE);
        const request = store.get(sessionId);

        request.onsuccess = () => {
          const session = request.result;
          if (session && session.messages) {
            // Convert timestamp strings back to Date objects
            const messages = session.messages.map((msg: any) => ({
              ...msg,
              timestamp: new Date(msg.timestamp),
            }));
            resolve(messages);
          } else {
            resolve([]);
          }
        };
        request.onerror = () => reject(request.error);
      });
    } catch (error) {
      console.error("Failed to load messages from IndexDB:", error);
      return [];
    }
  },

  /**
   * Load all messages from a specific session
   */
  loadMessagesBySessionId: async (sessionId: string): Promise<Message[]> => {
    try {
      const db = await indexdbService.initDB();

      return new Promise((resolve, reject) => {
        const transaction = db.transaction([SESSIONS_STORE], "readonly");
        const store = transaction.objectStore(SESSIONS_STORE);
        const request = store.get(sessionId);

        request.onsuccess = () => {
          const session = request.result;
          if (session && session.messages) {
            const messages = session.messages.map((msg: any) => ({
              ...msg,
              timestamp: new Date(msg.timestamp),
            }));
            resolve(messages);
          } else {
            resolve([]);
          }
        };
        request.onerror = () => reject(request.error);
      });
    } catch (error) {
      console.error("Failed to load messages by session from IndexDB:", error);
      return [];
    }
  },

  /**
   * Load all chat session history
   */
  loadSessions: async (): Promise<ChatSession[]> => {
    try {
      const db = await indexdbService.initDB();

      return new Promise((resolve, reject) => {
        const transaction = db.transaction([SESSIONS_STORE], "readonly");
        const store = transaction.objectStore(SESSIONS_STORE);
        const index = store.index("updatedAt");
        const request = index.getAll();

        request.onsuccess = () => {
          const sessions = request.result.sort(
            (a, b) =>
              new Date(b.updatedAt).getTime() - new Date(a.updatedAt).getTime()
          );
          resolve(sessions);
        };
        request.onerror = () => reject(request.error);
      });
    } catch (error) {
      console.error("Failed to load sessions from IndexDB:", error);
      return [];
    }
  },

  /**
   * Clear all messages from the current session
   */
  clearCurrentSession: async (): Promise<void> => {
    try {
      const db = await indexdbService.initDB();
      const sessionId = await indexdbService.getCurrentSessionId();

      return new Promise((resolve, reject) => {
        const transaction = db.transaction([SESSIONS_STORE], "readwrite");
        const store = transaction.objectStore(SESSIONS_STORE);
        const request = store.delete(sessionId);

        request.onsuccess = () => {
          // Clear the current session ID
          localStorage.removeItem(CURRENT_SESSION_KEY);
          resolve();
        };
        request.onerror = () => reject(request.error);
      });
    } catch (error) {
      console.error("Failed to clear current session:", error);
    }
  },

  /**
   * Delete all data from IndexDB
   */
  clearAllData: async (): Promise<void> => {
    try {
      return new Promise((resolve, reject) => {
        const request = indexedDB.deleteDatabase(DB_NAME);
        request.onsuccess = () => {
          localStorage.removeItem(CURRENT_SESSION_KEY);
          resolve();
        };
        request.onerror = () => reject(request.error);
      });
    } catch (error) {
      console.error("Failed to clear all IndexDB data:", error);
    }
  },

  /**
   * Delete a specific session permanently from IndexDB
   */
  deleteSession: async (sessionId: string): Promise<void> => {
    try {
      const db = await indexdbService.initDB();
      return new Promise((resolve, reject) => {
        const transaction = db.transaction([SESSIONS_STORE], "readwrite");
        const store = transaction.objectStore(SESSIONS_STORE);
        const request = store.delete(sessionId);
        request.onsuccess = () => {
          const current = localStorage.getItem(CURRENT_SESSION_KEY);
          if (current === sessionId) {
            localStorage.removeItem(CURRENT_SESSION_KEY);
          }
          resolve();
        };
        request.onerror = () => reject(request.error);
      });
    } catch (error) {
      console.error("Failed to delete session:", error);
    }
  },

  /**
   * Get or create a session ID - loads most recent session if none is active
   */
  getCurrentSessionId: async (): Promise<string> => {
    let sessionId = localStorage.getItem(CURRENT_SESSION_KEY);
    
    if (!sessionId) {
      // Try to load the most recent session from IndexDB
      try {
        const sessions = await indexdbService.loadSessions();
        if (sessions && sessions.length > 0) {
          // Load the most recent session
          sessionId = sessions[0].id;
          localStorage.setItem(CURRENT_SESSION_KEY, sessionId);
          return sessionId;
        }
      } catch (error) {
        console.error("Failed to load recent sessions:", error);
      }
      
      // If no existing sessions, create a new one
      sessionId = `session_${Date.now()}`;
      localStorage.setItem(CURRENT_SESSION_KEY, sessionId);
    }
    
    return sessionId;
  },

  /**
   * Create a new session (for starting a new chat)
   */
  createNewSession: async (): Promise<string> => {
    const newSessionId = `session_${Date.now()}`;
    localStorage.setItem(CURRENT_SESSION_KEY, newSessionId);
    return newSessionId;
  },

  /**
   * Load a specific session by ID
   */
  loadSession: async (sessionId: string): Promise<ChatSession | null> => {
    try {
      const db = await indexdbService.initDB();

      return new Promise((resolve, reject) => {
        const transaction = db.transaction([SESSIONS_STORE], "readonly");
        const store = transaction.objectStore(SESSIONS_STORE);
        const request = store.get(sessionId);

        request.onsuccess = () => {
          const session = request.result || null;
          if (session && session.messages) {
            // Convert timestamp strings back to Date objects
            session.messages = session.messages.map((msg: any) => ({
              ...msg,
              timestamp: new Date(msg.timestamp),
            }));
          }
          resolve(session);
        };
        request.onerror = () => reject(request.error);
      });
    } catch (error) {
      console.error("Failed to load session:", error);
      return null;
    }
  },

  /**
   * Switch to a different session
   */
  switchSession: async (sessionId: string): Promise<void> => {
    localStorage.setItem(CURRENT_SESSION_KEY, sessionId);
  },
};
