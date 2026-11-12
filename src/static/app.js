document.addEventListener("DOMContentLoaded", () => {
  const activitiesList = document.getElementById("activities-list");
  const activitySelect = document.getElementById("activity");
  const signupForm = document.getElementById("signup-form");
  const loginRequired = document.getElementById("login-required");
  const messageDiv = document.getElementById("message");
  const authStatus = document.getElementById("auth-status");
  const loginButton = document.getElementById("login-button");
  const logoutButton = document.getElementById("logout-button");
  const loginDialog = document.getElementById("login-dialog");
  const loginForm = document.getElementById("login-form");
  const loginError = document.getElementById("login-error");
  const cancelLoginButton = document.getElementById("cancel-login");
  let teacherLoggedIn = false;

  function updateAuthUI(authenticated) {
    teacherLoggedIn = authenticated;
    authStatus.textContent = authenticated
      ? "Logged in as teacher"
      : "Viewing activities";
    loginButton.classList.toggle("hidden", authenticated);
    logoutButton.classList.toggle("hidden", !authenticated);
    signupForm.hidden = !authenticated;
    loginRequired.hidden = authenticated;
  }

  function showMessage(text, type) {
    messageDiv.textContent = text;
    messageDiv.className = `message ${type}`;
    messageDiv.classList.remove("hidden");

    setTimeout(() => {
      messageDiv.classList.add("hidden");
    }, 5000);
  }

  async function fetchActivities() {
    try {
      const response = await fetch("/activities");
      if (!response.ok) {
        throw new Error("Unable to load activities");
      }

      const activities = await response.json();
      activitiesList.innerHTML = "";
      activitySelect.replaceChildren(activitySelect.options[0]);

      Object.entries(activities).forEach(([name, details]) => {
        const activityCard = document.createElement("div");
        activityCard.className = "activity-card";

        const spotsLeft =
          details.max_participants - details.participants.length;
        const participantsHTML =
          details.participants.length > 0
            ? `<div class="participants-section">
                <h5>Participants:</h5>
                <ul class="participants-list">
                  ${details.participants
                    .map(
                      (email) => `<li>
                        <span class="participant-email">${email}</span>
                        ${
                          teacherLoggedIn
                            ? `<button class="delete-btn" data-activity="${name}" data-email="${email}" aria-label="Unregister ${email} from ${name}">Unregister</button>`
                            : ""
                        }
                      </li>`
                    )
                    .join("")}
                </ul>
              </div>`
            : "<p><em>No participants yet</em></p>";

        activityCard.innerHTML = `
          <h4>${name}</h4>
          <p>${details.description}</p>
          <p><strong>Schedule:</strong> ${details.schedule}</p>
          <p><strong>Availability:</strong> ${spotsLeft} spots left</p>
          <div class="participants-container">${participantsHTML}</div>
        `;
        activitiesList.appendChild(activityCard);

        const option = document.createElement("option");
        option.value = name;
        option.textContent = name;
        activitySelect.appendChild(option);
      });

      document.querySelectorAll(".delete-btn").forEach((button) => {
        button.addEventListener("click", handleUnregister);
      });
    } catch (error) {
      activitiesList.innerHTML =
        "<p>Failed to load activities. Please try again later.</p>";
      console.error("Error fetching activities:", error);
    }
  }

  async function handleMutationResponse(response) {
    const result = await response.json();

    if (!response.ok) {
      if (response.status === 401) {
        updateAuthUI(false);
        await fetchActivities();
      }
      showMessage(result.detail || "An error occurred", "error");
      return false;
    }

    showMessage(result.message, "success");
    await fetchActivities();
    return true;
  }

  async function handleUnregister(event) {
    const button = event.currentTarget;
    const activity = button.getAttribute("data-activity");
    const email = button.getAttribute("data-email");

    try {
      const response = await fetch(
        `/activities/${encodeURIComponent(
          activity
        )}/unregister?email=${encodeURIComponent(email)}`,
        { method: "DELETE" }
      );
      await handleMutationResponse(response);
    } catch (error) {
      showMessage("Failed to unregister. Please try again.", "error");
      console.error("Error unregistering:", error);
    }
  }

  loginButton.addEventListener("click", () => {
    loginError.classList.add("hidden");
    loginDialog.showModal();
  });

  cancelLoginButton.addEventListener("click", () => {
    loginDialog.close();
  });

  loginForm.addEventListener("submit", async (event) => {
    event.preventDefault();
    loginError.classList.add("hidden");

    const formData = new FormData(loginForm);
    try {
      const response = await fetch("/auth/login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          username: formData.get("username"),
          password: formData.get("password"),
        }),
      });
      const result = await response.json();

      if (!response.ok) {
        throw new Error(result.detail || "Unable to log in");
      }

      loginForm.reset();
      loginDialog.close();
      updateAuthUI(true);
      await fetchActivities();
    } catch (error) {
      loginError.textContent = error.message;
      loginError.className = "error";
      console.error("Teacher login failed:", error);
    }
  });

  logoutButton.addEventListener("click", async () => {
    try {
      const response = await fetch("/auth/logout", { method: "POST" });
      const result = await response.json();
      if (!response.ok) {
        throw new Error(result.detail || "Unable to log out");
      }

      updateAuthUI(false);
      await fetchActivities();
      showMessage(result.message, "success");
    } catch (error) {
      showMessage("Failed to log out. Please try again.", "error");
      console.error("Teacher logout failed:", error);
    }
  });

  signupForm.addEventListener("submit", async (event) => {
    event.preventDefault();

    const email = document.getElementById("email").value;
    const activity = activitySelect.value;

    try {
      const response = await fetch(
        `/activities/${encodeURIComponent(
          activity
        )}/signup?email=${encodeURIComponent(email)}`,
        { method: "POST" }
      );
      await handleMutationResponse(response);
      if (response.ok) {
        signupForm.reset();
      }
    } catch (error) {
      showMessage("Failed to register the student. Please try again.", "error");
      console.error("Error registering student:", error);
    }
  });

  async function initialize() {
    try {
      const response = await fetch("/auth/session");
      if (!response.ok) {
        throw new Error("Unable to check teacher login status");
      }
      const session = await response.json();
      updateAuthUI(session.authenticated);
    } catch (error) {
      updateAuthUI(false);
      console.error("Error checking teacher login status:", error);
    }

    await fetchActivities();
  }

  initialize();
});
