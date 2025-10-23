// filename: server.js
// Run: npm install express axios

const express = require("express");
const axios = require("axios");

const app = express();
const PORT = process.env.PORT || 3000;

// ================= CONFIG =================
const PRIMARY_API = "https://osinttx.karobetahack.workers.dev?term={term}";
const SECONDARY_API = "https://family-members-n5um.vercel.app/fetch?aadhaar={id_number}&key=paidchx";
const OWNER_TAG = "@CyberHunter_HackBot";
const TIMEOUT = 20000; // 20 sec
// ==========================================

// Helper: Recursively find all 12-digit IDs
function findIdNumbers(obj) {
  const ids = new Set();
  const pattern = /^\d{12}$/;

  if (Array.isArray(obj)) {
    for (const item of obj) {
      const subIds = findIdNumbers(item);
      subIds.forEach(id => ids.add(id));
    }
  } else if (obj && typeof obj === "object") {
    for (const val of Object.values(obj)) {
      const subIds = findIdNumbers(val);
      subIds.forEach(id => ids.add(id));
    }
  } else if (typeof obj === "string") {
    if (pattern.test(obj)) {
      ids.add(obj);
    }
  }

  return ids;
}

// Helper: attach owner
function attachOwner(result) {
  if (typeof result === "object" && result !== null) {
    if (!result.owner) result.owner = OWNER_TAG;
    return result;
  } else {
    return { _value: result, owner: OWNER_TAG };
  }
}

// GET /api?num=...
app.get("/api", async (req, res) => {
  const num = req.query.num;

  // Validate input
  if (!num || !/^\d{10}$/.test(num)) {
    return res.status(400).json({ error: "num must be exactly 10 digits" });
  }

  try {
    // Primary API
    const primaryUrl = PRIMARY_API.replace("{term}", num);
    const primaryResp = await axios.get(primaryUrl, { timeout: TIMEOUT });
    const primaryData = primaryResp.data;
    const primaryWithOwner = attachOwner(primaryData);

    // Find 12-digit id_numbers
    const idNumbers = findIdNumbers(primaryData);
    const secondaryResults = {};

    // Secondary API calls if id_number exists
    for (const id of idNumbers) {
      try {
        const secUrl = SECONDARY_API.replace("{id_number}", id);
        const secResp = await axios.get(secUrl, { timeout: TIMEOUT });
        secondaryResults[id] = attachOwner(secResp.data);
      } catch (err) {
        secondaryResults[id] = attachOwner({ _error: err.message });
      }
    }

    // Combine response
    const combined = {
      primary: primaryWithOwner,
      secondary: Object.keys(secondaryResults).length ? secondaryResults : {},
      owner: OWNER_TAG,
    };

    res.json(combined);
  } catch (err) {
    res.json({
      primary: attachOwner({ _error: err.message }),
      secondary: {},
      owner: OWNER_TAG,
    });
  }
});

// Start server
app.listen(PORT, () => {
  console.log(`✅ API server running at http://localhost:${PORT}`);
});