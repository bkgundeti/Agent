document.getElementById("inputForm").addEventListener("submit", async function (e) {
  e.preventDefault();

  const form = new FormData();
  form.append("username", document.getElementById("username").value);
  form.append("requirement", document.getElementById("requirement").value);

  const resultBox = document.getElementById("resultBox");
  const resultContainer = document.getElementById("resultContainer");

  resultBox.textContent = "⏳ Processing your input... Please wait...";
  resultContainer.style.display = "block";

  try {
    const response = await fetch("/", {
      method: "POST",
      body: form,
    });

    const html = await response.text();
    const parser = new DOMParser();
    const doc = parser.parseFromString(html, "text/html");

    const newOutput = doc.querySelector("#output");
    if (newOutput) {
      resultBox.textContent = newOutput.textContent;
    } else {
      resultBox.textContent = "✅ Submitted successfully. Please check the recommendation above.";
    }

    // Auto-scroll to result
    resultContainer.scrollIntoView({ behavior: "smooth" });

  } catch (err) {
    resultBox.textContent = "❌ Error connecting to server.";
  }
});
