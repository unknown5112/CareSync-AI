// CareSync AI - Frontend Application Logic (XSS-Hardened, Offline-First, WCAG AAA Voice)

// Production API Base URL
const API_BASE_URL = "https://caresync-ai-we1r.onrender.com";
const SCAN_ENDPOINT = `${API_BASE_URL}/api/scan-medication`;
const INTERACTIONS_ENDPOINT = `${API_BASE_URL}/api/check-interactions`;
const CAREGIVER_ALERT_ENDPOINT = `${API_BASE_URL}/api/caregiver-alert`;

// DOM Elements
const appBody = document.getElementById("app-body");
const btnFontDec = document.getElementById("btn-font-dec");
const btnFontReset = document.getElementById("btn-font-reset");
const btnFontInc = document.getElementById("btn-font-inc");
const btnHighContrast = document.getElementById("btn-high-contrast");
const btnStopSpeech = document.getElementById("btn-stop-speech");
const srAnnouncer = document.getElementById("sr-announcer");

const passcodeInput = document.getElementById("passcode-input");
const keypadButtons = document.querySelectorAll(".keypad-btn");
const btnClear = document.getElementById("btn-clear");
const btnSubmitPin = document.getElementById("btn-submit-pin");
const loginFeedback = document.getElementById("login-feedback");
const loginSection = document.getElementById("login-section");
const userStatusPill = document.getElementById("user-status-pill");
const authStatusText = document.getElementById("auth-status-text");
const statusDot = document.getElementById("status-dot");

const adherencePct = document.getElementById("adherence-pct");
const adherenceCountLabel = document.getElementById("adherence-count-label");
const adherenceStatusPill = document.getElementById("adherence-status-pill");
const adherenceProgressFill = document.getElementById("adherence-progress-fill");
const scheduleSlotsContainer = document.getElementById("schedule-slots-container");

const ocrForm = document.getElementById("ocr-form");
const medicationFileInput = document.getElementById("medication-file-input");
const fileChosenBanner = document.getElementById("file-chosen-banner");
const fileNameText = document.getElementById("file-name-text");
const btnRemoveFile = document.getElementById("btn-remove-file");
const btnScan = document.getElementById("btn-scan");
const btnScanText = document.getElementById("btn-scan-text");
const btnScanSpinner = document.getElementById("btn-scan-spinner");

const scanResultCard = document.getElementById("scan-result-card");
const resultMedName = document.getElementById("result-med-name");
const resultDosage = document.getElementById("result-dosage");
const resultInstructions = document.getElementById("result-instructions");
const btnSpeakScan = document.getElementById("btn-speak-scan");
const btnDismissResult = document.getElementById("btn-dismiss-result");
const btnAddToSchedule = document.getElementById("btn-add-to-schedule");

const interactionBanner = document.getElementById("interaction-banner");
const interactionIcon = document.getElementById("interaction-icon");
const interactionTitle = document.getElementById("interaction-title");
const interactionSummary = document.getElementById("interaction-summary");
const interactionRec = document.getElementById("interaction-rec");

const inputCaregiverEmail = document.getElementById("input-caregiver-email");
const btnSaveCaregiver = document.getElementById("btn-save-caregiver");
const caregiverSaveFeedback = document.getElementById("caregiver-save-feedback");
const btnAlertMissed = document.getElementById("btn-alert-missed");
const btnAlertSos = document.getElementById("btn-alert-sos");

// State
let enteredPin = "";
let selectedCompressedBlob = null;
let currentFontSize = 100; // percent
let speechSynth = window.speechSynthesis || null;

// Default initial schedule for elderly demonstration
const DEFAULT_SCHEDULE = [
  { id: "slot-1", slot: "Morning", time: "08:00 AM", name: "Metformin (500mg)", notes: "Take 1 tablet with breakfast and water.", taken: true, icon: "🌅" },
  { id: "slot-2", slot: "Afternoon", time: "01:00 PM", name: "Lisinopril (10mg)", notes: "Take 1 tablet after lunch.", taken: false, icon: "☀️" },
  { id: "slot-3", slot: "Night", time: "09:00 PM", name: "Atorvastatin (20mg)", notes: "Take 1 tablet before bedtime.", taken: false, icon: "🌙" }
];

// ==========================================
// 1. Storage & Offline-First State Handling
// ==========================================
function getStoredSchedule() {
  try {
    const raw = localStorage.getItem("caresync_schedule");
    return raw ? JSON.parse(raw) : DEFAULT_SCHEDULE;
  } catch (e) {
    return DEFAULT_SCHEDULE;
  }
}

function saveStoredSchedule(schedule) {
  try {
    localStorage.setItem("caresync_schedule", JSON.stringify(schedule));
  } catch (e) {
    console.warn("localStorage quota exceeded", e);
  }
}

function getStoredCaregiverEmail() {
  return localStorage.getItem("caresync_caregiver_email") || "";
}

function announceToScreenReader(message) {
  if (srAnnouncer) {
    srAnnouncer.textContent = "";
    setTimeout(() => {
      srAnnouncer.textContent = message;
    }, 50);
  }
}

// ==========================================
// 2. Web Speech API (Calm Elderly Voice Rate)
// ==========================================
function speakText(text) {
  if (!speechSynth) {
    alert("Speech Synthesis is not supported in this browser.");
    return;
  }
  speechSynth.cancel(); // Stop any ongoing speech
  const utterance = new SpeechSynthesisUtterance(text);
  utterance.rate = 0.88; // Calm, deliberate pace for elderly listeners
  utterance.pitch = 1.0;
  speechSynth.speak(utterance);
}

btnStopSpeech.addEventListener("click", () => {
  if (speechSynth) speechSynth.cancel();
});

// ==========================================
// 3. Senior Accessibility Controls (Font & Contrast)
// ==========================================
btnFontInc.addEventListener("click", () => {
  if (currentFontSize < 140) {
    currentFontSize += 10;
    document.documentElement.style.fontSize = `${currentFontSize}%`;
    announceToScreenReader(`Text size increased to ${currentFontSize} percent`);
  }
});

btnFontDec.addEventListener("click", () => {
  if (currentFontSize > 90) {
    currentFontSize -= 10;
    document.documentElement.style.fontSize = `${currentFontSize}%`;
    announceToScreenReader(`Text size decreased to ${currentFontSize} percent`);
  }
});

btnFontReset.addEventListener("click", () => {
  currentFontSize = 100;
  document.documentElement.style.fontSize = "100%";
  announceToScreenReader("Text size reset to standard");
});

const isHighContrast = localStorage.getItem("caresync_high_contrast") === "true";
if (isHighContrast) {
  appBody.classList.add("high-contrast");
  btnHighContrast.setAttribute("aria-pressed", "true");
}

btnHighContrast.addEventListener("click", () => {
  const active = appBody.classList.toggle("high-contrast");
  btnHighContrast.setAttribute("aria-pressed", active ? "true" : "false");
  localStorage.setItem("caresync_high_contrast", active ? "true" : "false");
  announceToScreenReader(active ? "High contrast mode enabled" : "Standard contrast mode restored");
});

// ==========================================
// 4. Passcode Authentication
// ==========================================
keypadButtons.forEach((btn) => {
  btn.addEventListener("click", () => {
    if (enteredPin.length < 4) {
      enteredPin += btn.textContent.trim();
      updatePinDisplay();
      if (enteredPin.length === 4) {
        verifyPin();
      }
    }
  });
});

btnClear.addEventListener("click", () => {
  enteredPin = "";
  updatePinDisplay();
  loginFeedback.textContent = "Passcode cleared.";
  loginFeedback.className = "text-xl font-bold text-slate-600 min-h-[2rem]";
});

btnSubmitPin.addEventListener("click", verifyPin);

function updatePinDisplay() {
  passcodeInput.value = enteredPin ? "•".repeat(enteredPin.length) : "";
}

function verifyPin() {
  if (enteredPin === "1234" || enteredPin.length === 4) {
    loginFeedback.textContent = "✅ Access Granted! Welcome to CareSync AI.";
    loginFeedback.className = "text-xl font-bold text-green-700 min-h-[2rem]";
    authStatusText.textContent = "Senior Care Active";
    statusDot.className = "w-4 h-4 rounded-full bg-emerald-400";
    userStatusPill.className = "bg-emerald-900 border-2 border-emerald-500 rounded-full px-5 py-2.5 text-lg font-semibold flex items-center gap-3";

    announceToScreenReader("Access Granted. Showing your medication schedule.");
    setTimeout(() => {
      loginSection.classList.add("hidden");
    }, 500);
  } else {
    loginFeedback.textContent = "❌ Please enter your 4-digit code (Default: 1234).";
    loginFeedback.className = "text-xl font-bold text-red-600 min-h-[2rem]";
    announceToScreenReader("Invalid passcode. Please enter 4 digits.");
  }
}

// ==========================================
// 5. Adherence Dashboard & Dynamic Schedule (Zero innerHTML)
// ==========================================
function renderSchedule() {
  const schedule = getStoredSchedule();
  // Clear container using safe DOM methods
  while (scheduleSlotsContainer.firstChild) {
    scheduleSlotsContainer.removeChild(scheduleSlotsContainer.firstChild);
  }

  let takenCount = 0;

  schedule.forEach((item, index) => {
    if (item.taken) takenCount++;

    const article = document.createElement("article");
    article.className = `flex flex-col md:flex-row items-start md:items-center justify-between p-6 rounded-2xl border-4 gap-4 transition shadow-sm ${
      item.taken ? "border-green-500 bg-green-50" : "border-amber-400 bg-amber-50"
    }`;

    // Left info block
    const leftDiv = document.createElement("div");
    leftDiv.className = "flex items-center gap-5";

    const iconSpan = document.createElement("span");
    iconSpan.className = "text-5xl";
    iconSpan.setAttribute("role", "img");
    iconSpan.setAttribute("aria-hidden", "true");
    iconSpan.textContent = item.icon || "💊";

    const textDiv = document.createElement("div");

    const badgeSpan = document.createElement("span");
    badgeSpan.className = `inline-block text-white text-sm font-bold uppercase tracking-wider px-3 py-1 rounded-md mb-1 ${
      item.taken ? "bg-green-700" : "bg-amber-700"
    }`;
    badgeSpan.textContent = `${item.slot} • ${item.time}`;

    const titleH3 = document.createElement("h3");
    titleH3.className = "text-2xl sm:text-3xl font-extrabold text-slate-900";
    titleH3.textContent = item.name;

    const descP = document.createElement("p");
    descP.className = "text-xl text-slate-700 font-medium";
    descP.textContent = item.notes;

    textDiv.appendChild(badgeSpan);
    textDiv.appendChild(titleH3);
    textDiv.appendChild(descP);

    leftDiv.appendChild(iconSpan);
    leftDiv.appendChild(textDiv);

    // Right Action Buttons
    const actionDiv = document.createElement("div");
    actionDiv.className = "flex flex-col sm:flex-row items-center gap-3 w-full md:w-auto";

    // Voice button for card
    const speakBtn = document.createElement("button");
    speakBtn.type = "button";
    speakBtn.className = "bg-indigo-600 hover:bg-indigo-700 text-white font-bold py-3 px-4 rounded-xl text-base flex items-center gap-2";
    speakBtn.setAttribute("aria-label", `Listen to instructions for ${item.name}`);
    const speakIcon = document.createElement("span");
    speakIcon.textContent = "🔊";
    speakBtn.appendChild(speakIcon);
    speakBtn.appendChild(document.createTextNode("Listen"));
    speakBtn.addEventListener("click", () => {
      speakText(`Medication: ${item.name}. Scheduled for ${item.slot} at ${item.time}. Instructions: ${item.notes}. Status: ${item.taken ? "Already taken" : "Not yet taken"}.`);
    });

    // Toggle Taken Button
    const toggleBtn = document.createElement("button");
    toggleBtn.type = "button";
    toggleBtn.className = `w-full sm:w-auto text-white text-xl font-bold py-4 px-8 rounded-xl shadow-md transition transform active:scale-95 ${
      item.taken ? "bg-green-700 hover:bg-green-800" : "bg-amber-600 hover:bg-amber-700"
    }`;
    toggleBtn.textContent = item.taken ? "✓ Taken" : "Mark as Taken";
    toggleBtn.setAttribute("aria-label", `Mark ${item.name} as ${item.taken ? "untaken" : "taken"}`);

    toggleBtn.addEventListener("click", () => {
      schedule[index].taken = !schedule[index].taken;
      saveStoredSchedule(schedule);
      renderSchedule();
      announceToScreenReader(`${item.name} marked as ${schedule[index].taken ? "taken" : "pending"}`);
    });

    actionDiv.appendChild(speakBtn);
    actionDiv.appendChild(toggleBtn);

    article.appendChild(leftDiv);
    article.appendChild(actionDiv);

    scheduleSlotsContainer.appendChild(article);
  });

  // Update Adherence Progress Bar
  const total = schedule.length;
  const pct = total > 0 ? Math.round((takenCount / total) * 100) : 0;
  adherencePct.textContent = `${pct}%`;
  adherenceCountLabel.textContent = `${takenCount} of ${total} doses taken`;
  adherenceProgressFill.style.width = `${pct}%`;
  adherenceStatusPill.textContent = pct === 100 ? "🎉 Completed" : "In Progress";
  adherenceStatusPill.className = pct === 100 ? "text-green-700 font-extrabold" : "text-blue-700 font-extrabold";
}

// ==========================================
// 6. Client-Side Image Compression (<canvas>)
// ==========================================
async function compressImage(file, maxDimension = 1024, quality = 0.8) {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onerror = reject;
    reader.onload = (e) => {
      const img = new Image();
      img.onerror = reject;
      img.onload = () => {
        let width = img.width;
        let height = img.height;

        if (width > maxDimension || height > maxDimension) {
          if (width > height) {
            height = Math.round((height * maxDimension) / width);
            width = maxDimension;
          } else {
            width = Math.round((width * maxDimension) / height);
            height = maxDimension;
          }
        }

        const canvas = document.createElement("canvas");
        canvas.width = width;
        canvas.height = height;
        const ctx = canvas.getContext("2d");
        ctx.drawImage(img, 0, 0, width, height);

        canvas.toBlob(
          (blob) => {
            if (blob) {
              resolve(blob);
            } else {
              reject(new Error("Canvas compression failed"));
            }
          },
          "image/jpeg",
          quality
        );
      };
      img.src = e.target.result;
    };
    reader.readAsDataURL(file);
  });
}

// ==========================================
// 7. Robust Fetch with AbortController Timeout
// ==========================================
async function fetchWithTimeout(url, options = {}, timeoutMs = 45000) {
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), timeoutMs);
  try {
    const response = await fetch(url, {
      ...options,
      signal: controller.signal,
    });
    return response;
  } finally {
    clearTimeout(timeoutId);
  }
}

// ==========================================
// 8. File Upload & OCR Scan Handling
// ==========================================
medicationFileInput.addEventListener("change", async (e) => {
  const files = e.target.files;
  if (files && files.length > 0) {
    const originalFile = files[0];
    fileNameText.textContent = `Optimizing: ${originalFile.name}...`;
    fileChosenBanner.classList.remove("hidden");
    btnScan.disabled = true;

    try {
      selectedCompressedBlob = await compressImage(originalFile, 1024, 0.8);
      const compressedKb = Math.round(selectedCompressedBlob.size / 1024);
      fileNameText.textContent = `Ready: ${originalFile.name} (Compressed to ${compressedKb} KB)`;
      btnScan.disabled = false;
      announceToScreenReader(`Image optimized. Compressed size ${compressedKb} kilobytes.`);
    } catch (err) {
      console.warn("Client compression failed, using original file", err);
      selectedCompressedBlob = originalFile;
      fileNameText.textContent = `Ready: ${originalFile.name}`;
      btnScan.disabled = false;
    }
  }
});

btnRemoveFile.addEventListener("click", () => {
  selectedCompressedBlob = null;
  medicationFileInput.value = "";
  fileChosenBanner.classList.add("hidden");
  btnScan.disabled = true;
});

ocrForm.addEventListener("submit", async (e) => {
  e.preventDefault();
  if (!selectedCompressedBlob) return;

  btnScan.disabled = true;
  btnScanSpinner.classList.remove("hidden");
  btnScanText.textContent = "Analyzing Medication with Gemini AI...";
  announceToScreenReader("Analyzing medication image. Please wait.");

  const formData = new FormData();
  formData.append("file", selectedCompressedBlob, "medication_strip.jpg");

  try {
    const response = await fetchWithTimeout(SCAN_ENDPOINT, {
      method: "POST",
      body: formData,
    }, 45000);

    if (!response.ok) {
      const errJson = await response.json().catch(() => ({}));
      throw new Error(errJson.detail || `Server status ${response.status}`);
    }

    const result = await response.json();
    displayScanResult(result);
  } catch (error) {
    console.error("Gemini AI scan failed:", error);
    let msg = error.message;
    if (error.name === "AbortError") {
      msg = "Connection timed out. The backend server may be waking up. Please retry in a few seconds.";
    }
    alert(`Medication Scan Error: ${msg}`);
  } finally {
    btnScan.disabled = false;
    btnScanSpinner.classList.add("hidden");
    btnScanText.textContent = "🔍 Scan Medication With AI";
  }
});

async function displayScanResult(result) {
  const data = result.data || {};
  const medName = data.medication_name || "Unknown Medication";
  const dosage = data.suggested_dosage || data.strength || "Dosage as advised by doctor";
  const instructions = data.instructions || "Follow prescription guidelines and consult healthcare provider.";

  // Safe DOM text assignment (zero XSS vulnerability)
  resultMedName.textContent = medName;
  resultDosage.textContent = dosage;
  resultInstructions.textContent = instructions;

  scanResultCard.classList.remove("hidden");
  scanResultCard.scrollIntoView({ behavior: "smooth" });

  announceToScreenReader(`Medication scanned: ${medName}. Dosage: ${dosage}.`);

  // Wire Voice Read-Aloud for scanned result
  btnSpeakScan.onclick = () => {
    speakText(`Medication identified: ${medName}. Recommended dosage: ${dosage}. Instructions: ${instructions}.`);
  };

  // Automated Drug Interaction Check against current schedule
  checkDrugInteractions(medName);
}

// Automated Drug-Drug Interaction Safety Screening
async function checkDrugInteractions(newMedName) {
  const currentSchedule = getStoredSchedule();
  const currentMeds = currentSchedule.map((m) => m.name);

  if (currentMeds.length === 0) {
    interactionBanner.classList.add("hidden");
    return;
  }

  try {
    const response = await fetchWithTimeout(INTERACTIONS_ENDPOINT, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        new_medication: newMedName,
        current_medications: currentMeds,
      }),
    }, 30000);

    if (response.ok) {
      const result = await response.json();
      displayInteractionBanner(result);
    }
  } catch (err) {
    console.warn("Drug interaction check error:", err);
  }
}

function displayInteractionBanner(result) {
  const severity = (result.severity || "safe").toLowerCase();
  interactionBanner.classList.remove("hidden");

  // Reset classes
  interactionBanner.className = "my-4 p-5 rounded-xl border-4 flex flex-col gap-2 shadow";

  if (severity === "danger") {
    interactionBanner.classList.add("bg-red-100", "border-red-600", "text-red-950");
    interactionIcon.textContent = "🚨";
    interactionTitle.textContent = "High Risk Drug Interaction Detected!";
  } else if (severity === "caution") {
    interactionBanner.classList.add("bg-amber-100", "border-amber-500", "text-amber-950");
    interactionIcon.textContent = "⚠️";
    interactionTitle.textContent = "Caution: Potential Drug Interaction";
  } else {
    interactionBanner.classList.add("bg-green-100", "border-green-600", "text-green-950");
    interactionIcon.textContent = "✅";
    interactionTitle.textContent = "Interaction Screening: Safe";
  }

  interactionSummary.textContent = result.summary || "No severe adverse reaction identified.";
  interactionRec.textContent = `Doctor Recommendation: ${result.recommendation || "Verify with doctor."}`;

  // Voice announcement of interaction result
  const speechMessage = `Safety Screening Result: ${result.summary}. Recommendation: ${result.recommendation}`;
  announceToScreenReader(speechMessage);
}

btnDismissResult.addEventListener("click", () => {
  scanResultCard.classList.add("hidden");
  interactionBanner.classList.add("hidden");
});

// Add scanned medication to active schedule
btnAddToSchedule.addEventListener("click", () => {
  const medName = resultMedName.textContent;
  const dosage = resultDosage.textContent;
  const instructions = resultInstructions.textContent;

  const currentSchedule = getStoredSchedule();
  currentSchedule.push({
    id: `slot-${Date.now()}`,
    slot: "Custom",
    time: "As Prescribed",
    name: medName,
    notes: `${dosage} - ${instructions}`,
    taken: false,
    icon: "💊"
  });

  saveStoredSchedule(currentSchedule);
  renderSchedule();
  scanResultCard.classList.add("hidden");
  interactionBanner.classList.add("hidden");
  announceToScreenReader(`${medName} added to today's schedule.`);
});

// ==========================================
// 9. Caregiver Safety Panel & Email Alerts
// ==========================================
const savedEmail = getStoredCaregiverEmail();
if (savedEmail) {
  inputCaregiverEmail.value = savedEmail;
}

btnSaveCaregiver.addEventListener("click", () => {
  const email = inputCaregiverEmail.value.trim();
  if (email && email.includes("@")) {
    localStorage.setItem("caresync_caregiver_email", email);
    caregiverSaveFeedback.textContent = "✅ Saved!";
    announceToScreenReader("Caregiver contact email saved.");
    setTimeout(() => {
      caregiverSaveFeedback.textContent = "";
    }, 3000);
  } else {
    alert("Please enter a valid email address.");
  }
});

btnAlertMissed.addEventListener("click", () => {
  dispatchCaregiverAlert("missed_dose", "Patient missed an afternoon medication dose.");
});

btnAlertSos.addEventListener("click", () => {
  dispatchCaregiverAlert("sos", "Urgent SOS button pressed by patient on dashboard.");
});

async function dispatchCaregiverAlert(alertType, defaultDetails) {
  const email = inputCaregiverEmail.value.trim();
  if (!email || !email.includes("@")) {
    alert("Please enter and save a caregiver email address first.");
    inputCaregiverEmail.focus();
    return;
  }

  const btn = alertType === "sos" ? btnAlertSos : btnAlertMissed;
  const originalText = btn.textContent;
  btn.disabled = true;
  btn.textContent = "Sending Alert...";

  try {
    const response = await fetchWithTimeout(CAREGIVER_ALERT_ENDPOINT, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        caregiver_email: email,
        patient_name: "Senior Family Member",
        alert_type: alertType,
        details: defaultDetails,
      }),
    }, 20000);

    if (!response.ok) {
      throw new Error(`Server returned ${response.status}`);
    }

    alert(`✅ Notification Sent: Caregiver alert (${alertType}) successfully dispatched to ${email}.`);
    announceToScreenReader("Caregiver alert dispatched successfully.");
  } catch (err) {
    alert(`Alert Dispatch Failed: ${err.message}`);
  } finally {
    btn.disabled = false;
    btn.textContent = originalText;
  }
}

// Keyboard Accessibility: Escape key dismisses modals and scan result
document.addEventListener("keydown", (e) => {
  if (e.key === "Escape") {
    if (!scanResultCard.classList.contains("hidden")) {
      scanResultCard.classList.add("hidden");
      interactionBanner.classList.add("hidden");
      btnScan.focus();
    }
  }
});

// Initial boot
renderSchedule();
