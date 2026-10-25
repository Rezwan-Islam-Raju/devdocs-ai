(function () {
  "use strict";

  const API = "/api/v1";
  const TOKEN_KEY = "devdocs_token";

  const authScreen = document.getElementById("auth-screen");
  const authForm = document.getElementById("auth-form");
  const passwordInput = document.getElementById("auth-password");
  const nameInput = document.getElementById("auth-name");
  const nameField = document.getElementById("name-field");
  const authSwitch = document.getElementById("auth-switch");
  const submitButton = document.getElementById("auth-submit");
  const authError = document.getElementById("auth-error");
  const strengthWrap = document.getElementById("strength-wrap");
  const strengthLabel = document.getElementById("strength-label");
  const passwordToggle = document.getElementById("toggle-password");

  const state = {
    token: localStorage.getItem(TOKEN_KEY),
    user: null,
    workspaces: [],
    documents: [],
    activeWorkspaceId: null,
    registering: false,
  };

  // --------------------------------------------------
  // Utility functions
  // --------------------------------------------------

  function escapeHtml(value) {
    return String(value == null ? "" : value).replace(
      /[&<>"']/g,
      function (character) {
        return {
          "&": "&amp;",
          "<": "&lt;",
          ">": "&gt;",
          '"': "&quot;",
          "'": "&#39;",
        }[character];
      }
    );
  }

  async function request(path, options) {
    const settings = options || {};
    const headers = new Headers(settings.headers || {});

    if (state.token) {
      headers.set("Authorization", "Bearer " + state.token);
    }

    if (settings.body && !(settings.body instanceof FormData)) {
      headers.set("Content-Type", "application/json");
    }

    let response;

    try {
      response = await fetch(API + path, {
        ...settings,
        headers: headers,
      });
    } catch (error) {
      throw new Error(
        "Cannot reach the API. Check that the FastAPI server is running."
      );
    }

    const contentType = response.headers.get("content-type") || "";

    const payload =
      contentType.indexOf("application/json") !== -1
        ? await response.json()
        : await response.text();

    if (!response.ok) {
      const detail =
        payload && typeof payload === "object"
          ? payload.detail
          : payload;

      const message = Array.isArray(detail)
        ? detail
            .map(function (item) {
              return item.msg || "Invalid input";
            })
            .join(", ")
        : detail || "Request failed (" + response.status + ")";

      const error = new Error(message);
      error.status = response.status;

      if (response.status === 401 && state.token) {
        clearSession();
      }

      throw error;
    }

    return payload;
  }

  function clearSession() {
    state.token = null;
    state.user = null;
    state.workspaces = [];
    state.documents = [];
    state.activeWorkspaceId = null;

    localStorage.removeItem(TOKEN_KEY);
  }

  // --------------------------------------------------
  // Authentication
  // --------------------------------------------------

  function setAuthMode(registering) {
    state.registering = registering;
    authError.textContent = "";

    document.getElementById("auth-title").textContent = registering
      ? "Create your account"
      : "Welcome back";

    document.getElementById("auth-subtitle").textContent = registering
      ? "Start turning your docs into answers."
      : "Sign in to pick up where you left off.";

    document.getElementById("auth-switch-copy").textContent = registering
      ? "Already have an account?"
      : "New to Rezifa AI?";

    authSwitch.textContent = registering ? "Sign in" : "Create an account";

    nameField.classList.toggle("hidden", !registering);
    nameInput.required = registering;

    passwordInput.autocomplete = registering
      ? "new-password"
      : "current-password";

    submitButton.querySelector(
      "[data-auth-submit-label]"
    ).textContent = registering ? "Create account" : "Sign in";

    updatePasswordStrength();
  }

  function updatePasswordStrength() {
    const password = passwordInput.value;

    if (!state.registering || !password) {
      strengthWrap.classList.add("hidden");
      strengthWrap.classList.remove("flex");
      return;
    }

    let score = 0;

    if (password.length >= 8) score += 1;

    if (/[A-Z]/.test(password) && /[a-z]/.test(password)) {
      score += 1;
    }

    if (/\d/.test(password)) {
      score += 1;
    }

    if (/[^A-Za-z0-9]/.test(password) || password.length >= 14) {
      score += 1;
    }

    score = Math.max(score, 1);

    const colors = ["#f43f5e", "#f59e0b", "#84cc16", "#10b981"];
    const names = ["Weak", "Fair", "Good", "Strong"];

    strengthWrap.classList.remove("hidden");
    strengthWrap.classList.add("flex");

    strengthWrap.querySelectorAll("[data-bar]").forEach(function (bar, index) {
      bar.style.backgroundColor = index < score ? colors[score - 1] : "";
    });

    strengthLabel.textContent = names[score - 1];
    strengthLabel.style.color = colors[score - 1];
  }

  passwordInput.addEventListener("input", updatePasswordStrength);

  passwordToggle.addEventListener("click", function () {
    const showing = passwordInput.type === "password";

    passwordInput.type = showing ? "text" : "password";

    passwordToggle.setAttribute(
      "aria-label",
      showing ? "Hide password" : "Show password"
    );

    passwordToggle.setAttribute("aria-pressed", String(showing));
  });

  authSwitch.addEventListener("click", function () {
    setAuthMode(!state.registering);
  });

  authForm.addEventListener("submit", async function (event) {
    event.preventDefault();

    authError.textContent = "";

    if (!authForm.reportValidity()) return;

    const email = document.getElementById("auth-email").value.trim();
    const password = passwordInput.value;

    submitButton.disabled = true;

    submitButton.querySelector(
      "[data-auth-submit-label]"
    ).textContent = state.registering
      ? "Creating account..."
      : "Signing in...";

    try {
      if (state.registering) {
        await request("/auth/register", {
          method: "POST",
          body: JSON.stringify({
            name: nameInput.value.trim(),
            email: email,
            password: password,
          }),
        });
      }

      const login = await request("/auth/login", {
        method: "POST",
        body: JSON.stringify({
          email: email,
          password: password,
        }),
      });

      state.token = login.access_token;

      localStorage.setItem(TOKEN_KEY, state.token);

      state.user = await request("/auth/");

      await renderDashboard();
    } catch (error) {
      authError.textContent = error.message;

      if (state.registering && error.status === 401) {
        setAuthMode(false);

        authError.textContent =
          "Account created, but sign-in failed. Please sign in with your new account.";
      }
    } finally {
      submitButton.disabled = false;

      submitButton.querySelector(
        "[data-auth-submit-label]"
      ).textContent = state.registering
        ? "Create account"
        : "Sign in";
    }
  });

  // --------------------------------------------------
  // Dashboard
  // --------------------------------------------------

  function renderDashboard() {
    authScreen.innerHTML = `
      <main class="dashboard-shell">

        <aside class="dashboard-sidebar">

          <a href="/" class="dashboard-brand" aria-label="Rezifa AI home">
            <img class="dashboard-brand-mark" src="/static/rezifa-mark.svg" alt="">
            <span>Rezifa<span class="dashboard-brand-accent"> AI</span></span>
          </a>

          <p class="dashboard-nav-label">WORKSPACE</p>

          <nav class="dashboard-nav" aria-label="Dashboard">
            <a href="#overview" data-dashboard-nav class="dashboard-nav-link is-active">
              <span>01</span> Overview
            </a>

            <a href="#workspaces" data-dashboard-nav class="dashboard-nav-link">
              <span>02</span> Workspaces
            </a>

            <a href="#documents" data-dashboard-nav class="dashboard-nav-link">
              <span>03</span> Documents
            </a>

            <a href="#ask-ai" data-dashboard-nav class="dashboard-nav-link">
              <span>04</span> Ask AI
            </a>
          </nav>

          <div class="dashboard-sidebar-footer">
            <div class="dashboard-user">
              <span class="dashboard-avatar">
                ${escapeHtml((state.user.name || "U").charAt(0).toUpperCase())}
              </span>

              <span class="dashboard-user-copy">
                <strong>${escapeHtml(state.user.name)}</strong>
                <small>Personal workspace</small>
              </span>
            </div>
          </div>

        </aside>

        <div class="dashboard-main">

          <header class="dashboard-topbar">
            <div>
              <span class="dashboard-eyebrow">YOUR WORKSPACE</span>
              <span class="dashboard-topbar-title">Overview</span>
            </div>

            <div class="dashboard-topbar-actions">
              <span class="dashboard-online">
                <span></span> Workspace ready
              </span>

              <button
                id="sign-out"
                type="button"
                class="dashboard-signout dashboard-topbar-signout"
              >
                Sign out
              </button>
            </div>
          </header>

          <div class="dashboard-content">

            <section id="overview" class="dashboard-hero">
              <div class="dashboard-hero-glow"></div>

              <div class="dashboard-hero-copy">
                <p class="dashboard-hero-eyebrow">Your knowledge hub</p>

                <h1>Welcome, ${escapeHtml(state.user.name)}.</h1>

                <p>
                  Create a workspace, add your documentation,
                  and ask questions grounded in your files.
                  You can also chat with AI without uploading documents.
                </p>

                <div class="dashboard-hero-actions">
                  <a href="#workspaces" class="dashboard-hero-action">
                    Create a workspace
                    <span aria-hidden="true">&rarr;</span>
                  </a>
                  <a
                    href="#ask-ai"
                    class="dashboard-hero-action dashboard-hero-action-secondary"
                  >
                    Ask Rezifa AI
                    <span aria-hidden="true">&rarr;</span>
                  </a>
                </div>
              </div>

              <div class="dashboard-hero-art" aria-hidden="true">
                <span class="dashboard-orbit dashboard-orbit-one"></span>
                <span class="dashboard-orbit dashboard-orbit-two"></span>
                <span class="dashboard-orbit dashboard-orbit-three"></span>
                <span class="dashboard-hero-core">
                  <img src="/static/rezifa-mark.svg" alt="">
                </span>
              </div>
            </section>

            <div class="dashboard-stats" aria-label="Workspace summary">

              <article class="dashboard-stat">
                <span class="dashboard-stat-label">WORKSPACES</span>
                <strong id="workspace-count">0</strong>
                <span class="dashboard-stat-note">Organized projects</span>
              </article>

              <article class="dashboard-stat">
                <span class="dashboard-stat-label">DOCUMENTS</span>
                <strong id="document-count">0</strong>
                <span class="dashboard-stat-note">In selected workspace</span>
              </article>

              <article class="dashboard-stat dashboard-stat-tip">
                <span class="dashboard-stat-label">GET STARTED</span>
                <strong>Upload your docs</strong>
                <span class="dashboard-stat-note">
                  Then ask questions with sources
                </span>
              </article>

            </div>

            <div class="dashboard-section-heading">
              <div>
                <p class="dashboard-section-kicker">YOUR PROJECTS</p>
                <h2>Knowledge workspace</h2>
                <p>
                  Organize your files and get answers from your documentation.
                </p>
              </div>
            </div>

            <div class="dashboard-grid">

              <section id="workspaces" class="dashboard-card dashboard-workspaces">

                <div class="dashboard-card-heading">
                  <span class="dashboard-card-icon">01</span>

                  <div>
                    <h2>Workspaces</h2>
                    <p>Keep documentation organized by project.</p>
                  </div>
                </div>

                <form id="workspace-form" class="dashboard-form">

                  <label for="workspace-name">Workspace name</label>

                  <input
                    id="workspace-name"
                    required
                    maxlength="100"
                    placeholder="e.g. Product docs"
                  >

                  <label for="workspace-description">
                    Description <span>(optional)</span>
                  </label>

                  <input
                    id="workspace-description"
                    maxlength="500"
                    placeholder="What is this workspace for?"
                  >

                  <button type="submit" class="dashboard-primary-button">
                    Create workspace
                    <span aria-hidden="true">&rarr;</span>
                  </button>

                </form>

                <div class="dashboard-list-heading">
                  <h3>Your workspaces</h3>
                  <span id="workspace-list-count">0</span>
                </div>

                <div id="workspace-list" class="dashboard-workspace-list"></div>

              </section>

              <div class="dashboard-right-column">

                <section id="documents" class="dashboard-card">

                  <div class="dashboard-card-heading">
                    <span class="dashboard-card-icon">02</span>

                    <div>
                      <h2>Documents</h2>
                      <p>Upload PDF, TXT, or Markdown files.</p>
                    </div>
                  </div>

                  <label class="dashboard-field-label" for="upload-workspace">
                    Workspace
                  </label>

                  <select id="upload-workspace" class="dashboard-control"></select>

                  <label class="dashboard-field-label" for="document-file">
                    Choose a file
                  </label>

                  <input
                    id="document-file"
                    type="file"
                    accept=".pdf,.txt,.md"
                    class="dashboard-file-input"
                  >

                  <button
                    id="upload-document"
                    type="button"
                    class="dashboard-secondary-button"
                  >
                    Upload document
                  </button>

                  <div class="dashboard-list-heading">
                    <h3>Recent files</h3>
                  </div>

                  <div id="document-list" class="dashboard-document-list"></div>

                </section>

                <section id="ask-ai" class="dashboard-card dashboard-chat-card">

                  <div class="dashboard-card-heading">
                    <span class="dashboard-card-icon dashboard-chat-brand">
                      <img src="/static/rezifa-mark.svg" alt="">
                    </span>

                    <div>
                      <h2>Ask Rezifa AI</h2>
                      <p>
                        Ask general questions or get answers from your documents.
                      </p>
                    </div>
                  </div>

                  <div
                    id="chat-mode-status"
                    class="text-xs text-slate-500"
                    aria-live="polite"
                  >
                    General AI is available without a workspace.
                  </div>

                  <div
                    id="chat-messages"
                    class="dashboard-chat-messages"
                    aria-live="polite"
                  >
                    <p class="dashboard-chat-empty">
                      Ask me anything, or select a workspace to ask about your docs.
                    </p>
                  </div>

                  <form id="chat-form" class="dashboard-chat-form">

                    <textarea
                      id="chat-question"
                      required
                      rows="3"
                      placeholder="Ask Rezifa AI anything..."
                    ></textarea>

                    <button type="submit" class="dashboard-primary-button">
                      <span class="dashboard-chat-submit-label">Send</span>
                      <span aria-hidden="true">&uarr;</span>
                    </button>

                  </form>

                </section>

              </div>
            </div>

            <p id="app-notice" role="status" aria-live="polite" class="dashboard-notice"></p>

            <footer class="dashboard-credit">
              Developed with care by <strong>Rezwan</strong>
            </footer>

          </div>
        </div>
      </main>
    `;

    document.getElementById("sign-out").addEventListener("click", function () {
      clearSession();
      window.location.reload();
    });

    document.querySelectorAll("[data-dashboard-nav]").forEach(function (link) {
      link.addEventListener("click", function () {
        document.querySelectorAll("[data-dashboard-nav]").forEach(function (item) {
          item.classList.toggle("is-active", item === link);
        });
      });
    });

    document
      .getElementById("workspace-form")
      .addEventListener("submit", createWorkspace);

    document
      .getElementById("upload-workspace")
      .addEventListener("change", function (event) {
        state.activeWorkspaceId = Number(event.target.value) || null;
        loadWorkspaces().catch(showNotice);
      });

    document
      .getElementById("upload-document")
      .addEventListener("click", uploadDocument);

    document
      .getElementById("chat-form")
      .addEventListener("submit", askQuestion);

    document
      .getElementById("chat-question")
      .addEventListener("input", function (event) {
        const input = event.currentTarget;
        input.style.height = "auto";
        input.style.height = Math.min(input.scrollHeight, 160) + "px";
        input.style.overflowY = input.scrollHeight > 160 ? "auto" : "hidden";
      });

    updateChatMode();

    return loadWorkspaces();
  }

  // --------------------------------------------------
  // Workspace management
  // --------------------------------------------------

  async function loadWorkspaces() {
    try {
      state.workspaces = await request("/workspaces/");

      document.getElementById("workspace-count").textContent =
        String(state.workspaces.length);

      document.getElementById("workspace-list-count").textContent =
        String(state.workspaces.length);

      if (
        !state.workspaces.some(function (item) {
          return item.id === state.activeWorkspaceId;
        })
      ) {
        state.activeWorkspaceId = state.workspaces.length
          ? state.workspaces[0].id
          : null;
      }

      const list = document.getElementById("workspace-list");
      const picker = document.getElementById("upload-workspace");

      if (!state.workspaces.length) {
        list.innerHTML = `
          <p class="rounded-xl border border-dashed border-slate-300 p-5 text-sm text-slate-500">
            No workspace yet. You can still use general AI chat.
            Create a workspace to upload documents.
          </p>
        `;

        picker.innerHTML = '<option value="">No workspace selected</option>';
      } else {
        list.innerHTML = state.workspaces
          .map(function (workspace) {
            return `
              <button
                type="button"
                data-workspace-id="${workspace.id}"
                class="flex w-full items-center justify-between gap-3 rounded-xl border px-4 py-3 text-left transition ${
                  workspace.id === state.activeWorkspaceId
                    ? "border-violet-200 bg-violet-50"
                    : "border-slate-200 bg-white hover:bg-slate-50"
                }"
              >
                <span class="min-w-0">
                  <strong class="block truncate text-sm text-slate-800">
                    ${escapeHtml(workspace.name)}
                  </strong>

                  <span class="mt-1 block truncate text-xs text-slate-500">
                    ${escapeHtml(workspace.description || "Documentation workspace")}
                  </span>
                </span>

                <span class="shrink-0 text-xs font-medium text-violet-700">
                  Select →
                </span>
              </button>
            `;
          })
          .join("");

        picker.innerHTML = `
          <option value="">General AI — no workspace</option>
          ${
            state.workspaces
              .map(function (workspace) {
                return `
                  <option value="${workspace.id}">
                    ${escapeHtml(workspace.name)}
                  </option>
                `;
              })
              .join("")
          }
        `;

        picker.value = state.activeWorkspaceId
          ? String(state.activeWorkspaceId)
          : "";

        list.querySelectorAll("[data-workspace-id]").forEach(function (button) {
          button.addEventListener("click", function () {
            state.activeWorkspaceId = Number(button.dataset.workspaceId);
            loadWorkspaces().catch(showNotice);
          });
        });
      }

      updateChatMode();

      await refreshDocuments();
    } catch (error) {
      showNotice(error);
    }
  }

  function updateChatMode() {
    const status = document.getElementById("chat-mode-status");
    const input = document.getElementById("chat-question");

    if (!status || !input) return;

    if (state.activeWorkspaceId) {
      const workspace = state.workspaces.find(function (item) {
        return item.id === state.activeWorkspaceId;
      });

      status.textContent = workspace
        ? "Workspace mode: " + workspace.name + ". Relevant documents will be searched."
        : "Workspace mode: documents will be searched.";

      input.placeholder = "Ask a question about your documents...";
    } else {
      status.textContent =
        "General AI mode: ask anything without a workspace or documents.";

      input.placeholder = "Ask Rezifa AI anything...";
    }
  }

  // --------------------------------------------------
  // Document management
  // --------------------------------------------------

  async function refreshDocuments() {
    const list = document.getElementById("document-list");

    if (!state.activeWorkspaceId) {
      state.documents = [];

      document.getElementById("document-count").textContent = "0";

      list.innerHTML = `
        <p class="text-sm text-slate-500">
          Select a workspace to view documents. General AI works without one.
        </p>
      `;

      return;
    }

    state.documents = await request(
      "/documents/?workspace_id=" + state.activeWorkspaceId
    );

    document.getElementById("document-count").textContent =
      String(state.documents.length);

    list.innerHTML = state.documents.length
      ? state.documents
          .map(function (document) {
            const status = String(document.status || "PENDING").toLowerCase();

            return `
              <div class="flex items-center justify-between gap-3 rounded-xl bg-slate-50 px-3.5 py-3">
                <span class="min-w-0 truncate text-sm font-medium text-slate-700">
                  ${escapeHtml(document.file_name)}
                </span>

                <span class="shrink-0 rounded-full bg-white px-2.5 py-1 text-[11px] font-semibold text-slate-600">
                  ${escapeHtml(status)}
                </span>
              </div>
            `;
          })
          .join("")
      : `
        <p class="text-sm text-slate-500">
          No documents in this workspace yet.
        </p>
      `;
  }

  async function createWorkspace(event) {
    event.preventDefault();

    const form = event.currentTarget;
    const button = form.querySelector("button[type=submit]");

    button.disabled = true;

    try {
      const workspace = await request("/workspaces/", {
        method: "POST",
        body: JSON.stringify({
          name: document.getElementById("workspace-name").value.trim(),
          description:
            document.getElementById("workspace-description").value.trim() || "",
        }),
      });

      state.activeWorkspaceId = workspace.id;

      form.reset();

      await loadWorkspaces();

      showNotice("Workspace created.");
    } catch (error) {
      showNotice(error);
    } finally {
      button.disabled = false;
    }
  }

  async function uploadDocument() {
    const fileInput = document.getElementById("document-file");
    const file = fileInput.files[0];

    if (!state.activeWorkspaceId) {
      return showNotice(
        new Error("Select or create a workspace before uploading a document.")
      );
    }

    if (!file) {
      return showNotice(
        new Error("Choose a PDF, TXT, or Markdown file to upload.")
      );
    }

    if (!/\.(pdf|txt|md)$/i.test(file.name)) {
      return showNotice(
        new Error("Only PDF, TXT, and Markdown files are supported.")
      );
    }

    const button = document.getElementById("upload-document");
    const body = new FormData();

    body.append("workspace_id", String(state.activeWorkspaceId));
    body.append("file", file);

    button.disabled = true;

    try {
      await request("/documents/upload", {
        method: "POST",
        body: body,
      });

      fileInput.value = "";

      await refreshDocuments();

      showNotice("Upload received. Document processing has started.");
    } catch (error) {
      showNotice(error);
    } finally {
      button.disabled = false;
    }
  }

  // --------------------------------------------------
  // Chat messages
  // --------------------------------------------------

  function addChatMessage(role, text, sources) {
    const messages = document.getElementById("chat-messages");

    const emptyState = messages.querySelector(".dashboard-chat-empty");

    if (emptyState) {
      emptyState.remove();
    }

    const item = document.createElement("article");
    item.className =
      "dashboard-chat-message " +
      (role === "You" ? "is-user" : "is-assistant");

    const title = document.createElement("p");
    title.className =
      "mb-1 text-[11px] font-bold uppercase tracking-wide text-slate-500";
    title.textContent = role;

    const content = document.createElement("p");
    content.className = "whitespace-pre-wrap text-sm leading-6 text-slate-700";
    content.textContent = text;

    item.append(title, content);

    if (sources && sources.length) {
      const sourceList = document.createElement("p");

      sourceList.className = "mt-2 text-xs text-violet-700";

      sourceList.textContent =
        "Sources: " +
        sources
          .map(function (source) {
            return (
              source.file_name +
              " (chunk " +
              (Number(source.chunk_index) + 1) +
              ")"
            );
          })
          .join(", ");

      item.append(sourceList);
    }

    messages.append(item);
    messages.scrollTop = messages.scrollHeight;

    return item;
  }

  // --------------------------------------------------
  // Ask AI
  // --------------------------------------------------

  async function askQuestion(event) {
    event.preventDefault();

    const input = document.getElementById("chat-question");
    const question = input.value.trim();

    if (!question) return;

    addChatMessage("You", question);

    input.value = "";
    input.style.height = "";
    input.style.overflowY = "hidden";

    const waiting = addChatMessage(
      "Rezifa AI",
      state.activeWorkspaceId
        ? "Searching your workspace documents..."
        : "Thinking..."
    );

    const button = event.currentTarget.querySelector("button[type=submit]");

    button.disabled = true;

    try {
      const result = await request("/chat", {
        method: "POST",
        body: JSON.stringify({
          question: question,
          workspace_id: state.activeWorkspaceId || null,
        }),
      });

      waiting.remove();

      addChatMessage(
        "Rezifa AI",
        result.answer || "No answer was returned by the AI.",
        result.sources || []
      );
    } catch (error) {
      waiting.remove();

      addChatMessage("Rezifa AI", error.message);
    } finally {
      button.disabled = false;
    }
  }

  // --------------------------------------------------
  // Notifications
  // --------------------------------------------------

  function showNotice(error) {
    const notice = document.getElementById("app-notice");

    if (notice) {
      notice.textContent = error.message || String(error);
    }
  }

  // --------------------------------------------------
  // Initialize application
  // --------------------------------------------------

  async function initialize() {
    setAuthMode(false);

    if (!state.token) return;

    try {
      state.user = await request("/auth/");

      await renderDashboard();
    } catch (error) {
      if (error.status !== 401) {
        authError.textContent = error.message;
      }
    }
  }

  initialize();
})();
